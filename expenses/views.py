"""Views powering Ledgerly's expense tracking experience."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from .currencies import (
    DEFAULT_CURRENCY,
    MAX_CENTS,
    get_currency_symbol,
    parse_display_amount_to_cents,
)
from .forms import CurrencySettingsForm, TransactionForm
from .models import Category, Transaction, UserSettings


def _is_ajax(request) -> bool:
    """Return ``True`` when the request originated from an AJAX call."""

    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _filter_transactions(queryset, search_query):
    """Apply case-insensitive filtering across transaction fields."""

    if not search_query:
        return queryset

    return queryset.filter(
        Q(note__icontains=search_query)
        | Q(category__name__icontains=search_query)
        | Q(type__icontains=search_query)
        | Q(name__icontains=search_query)
    )


def _cycle_month_shift(reference: date, months: int, cycle_day: int) -> date:
    """Shift ``reference`` by whole months while keeping the cycle day."""

    year = reference.year + (reference.month - 1 + months) // 12
    month = (reference.month - 1 + months) % 12 + 1
    day = min(cycle_day, monthrange(year, month)[1])
    return date(year, month, day)


@login_required
def dashboard(request):
    """Render the main dashboard with transaction form and monthly stats."""

    # Only show active categories so users can classify transactions.
    categories = Category.objects.filter(is_active=True)

    # Persist per-user configuration such as cycle start date.
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    currency_symbol = get_currency_symbol(currency_code)

    # Limit transactions to the logged-in user for data isolation.
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .order_by('-occurred_on')
    )

    # Calculate cycle-aware stats based on the configured cycle start day.
    today = timezone.localdate()
    if settings_obj.cycle_start_date:
        cycle_day = settings_obj.cycle_start_date.day
    else:
        cycle_day = 1
    cycle_candidate = _cycle_month_shift(today, 0, cycle_day)
    if cycle_candidate > today:
        current_cycle_start = _cycle_month_shift(today, -1, cycle_day)
    else:
        current_cycle_start = cycle_candidate
    next_cycle_start = _cycle_month_shift(current_cycle_start, 1, cycle_day)

    cycle_transactions = transactions.filter(
        occurred_on__gte=current_cycle_start,
        occurred_on__lt=next_cycle_start,
    )
    income = (
        cycle_transactions
        .filter(type='INCOME')
        .aggregate(total=models.Sum('amount_in_cents'))['total']
        or 0
    )

    # Allow quick filtering from the dashboard search box.
    search_query = request.GET.get('q', '').strip()
    filtered_transactions = _filter_transactions(transactions, search_query)

    spend_history = cycle_transactions[:10]
    search_results = list(filtered_transactions[:15]) if search_query else []
    top_expenses = (
        cycle_transactions
        .filter(type='OUTGO')
        .order_by('-amount_in_cents')[:3]
    )
    outgo = (
        cycle_transactions
        .filter(type='OUTGO')
        .aggregate(total=models.Sum('amount_in_cents'))['total']
        or 0
    )
    balance = income - outgo

    top_spend = (
        cycle_transactions
        .filter(type='OUTGO')
        .order_by('-amount_in_cents')
        .first()
    )

    # Build cycle labels and totals for the past 12 cycles (oldest -> newest).
    cycle_starts = [
        _cycle_month_shift(current_cycle_start, -offset, cycle_day)
        for offset in range(11, -1, -1)
    ]
    months = [
        start.strftime('%Y-%m-%d')
        for start in cycle_starts
    ]
    income_data = []
    expense_data = []
    for start in cycle_starts:
        end = _cycle_month_shift(start, 1, cycle_day)
        cycle_window = transactions.filter(
            occurred_on__gte=start,
            occurred_on__lt=end,
        )
        window_totals = cycle_window.aggregate(
            income_total=Sum('amount_in_cents', filter=Q(type='INCOME')),
            expense_total=Sum('amount_in_cents', filter=Q(type='OUTGO')),
        )
        income_data.append(window_totals['income_total'] or 0)
        expense_data.append(window_totals['expense_total'] or 0)

    if request.method == 'POST':
        # Determine which inline modal submitted the request.
        action = request.POST.get('action', 'add_transaction')

        if action == 'update_cycle_start':
            cycle_start_raw = request.POST.get('cycle_start_date')
            if cycle_start_raw:
                # Store the user's preferred cycle anchor day
                # so future queries align with their reporting window.
                settings_obj.cycle_start_date = cycle_start_raw
                settings_obj.save(update_fields=['cycle_start_date'])
            return redirect('dashboard')

        # Default: persist the new transaction from the submitted form.
        # Missing category values are stored as NULL to keep records flexible.
        category_id = request.POST.get('category') or None
        if request.POST['type'] == 'OUTGO' and category_id is None:
            messages.error(
                request,
                'Outgoing transactions require a category. '
                'Please choose one before saving.',
            )
            return redirect('dashboard')

        amount_raw = (request.POST.get('amount_in_cents') or '').strip()
        if not amount_raw:
            messages.error(
                request,
                'Please enter an amount before saving the transaction.',
            )
            return redirect('dashboard')
        try:
            amount_cents = parse_display_amount_to_cents(amount_raw)
        except (InvalidOperation, ValueError):
            messages.error(
                request,
                'Amount must be a number using up to two decimal places '
                'for cents or pence (e.g., 12.50).',
            )
            return redirect('dashboard')

        if amount_cents <= 0:
            messages.error(
                request,
                'Amount must be greater than zero.',
            )
            return redirect('dashboard')
        if amount_cents > MAX_CENTS:
            messages.error(
                request,
                'That amount is too large for Ledgerly to store. '
                'Please enter a smaller value.',
            )
            return redirect('dashboard')

        Transaction.objects.create(
            user=request.user,
            name=request.POST['name'],
            type=request.POST['type'],
            amount_in_cents=amount_cents,
            category_id=category_id,
            occurred_on=request.POST['occurred_on'],
            note=request.POST.get('note', ''),
        )
        messages.success(
            request,
            'Income saved successfully.'
            if request.POST['type'] == 'INCOME'
            else 'Expense saved successfully.',
        )
        return redirect('dashboard')

    context = {
        # Pass full category list to the form.
        'categories': categories,
        # Show the 10 most recent transactions on the dashboard.
        'transactions': spend_history,
        'income': income,
        'outgo': outgo,
        'balance': balance,
        'top_spend': top_spend,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data,
        'search_query': search_query,
        'search_results': search_results,
        'top_expenses': top_expenses,
        'cycle_display_start': current_cycle_start,
        'cycle_setting_start': settings_obj.cycle_start_date,
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
        'max_transaction_amount': str(
            (Decimal(MAX_CENTS) / Decimal(100)).quantize(Decimal('0.00'))
        ),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def transaction_list(request):
    """Show the full history of a user's transactions."""

    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .order_by('-occurred_on')
    )
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    currency_symbol = get_currency_symbol(currency_code)
    return render(request, 'expenses/transaction_list.html', {
        'transactions': transactions,
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
    })


@login_required
def transaction_detail(request, pk):
    """Display and allow editing of a single transaction."""

    transaction = get_object_or_404(
        Transaction, pk=pk, user=request.user
    )

    ajax = _is_ajax(request)
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    currency_symbol = get_currency_symbol(currency_code)

    if request.method == 'POST':
        form = TransactionForm(
            request.POST,
            instance=transaction,
            currency_code=currency_code,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            if ajax:
                return JsonResponse({'success': True})
            return redirect('transaction_detail', pk=transaction.pk)
        if ajax:
            html = render_to_string(
                'expenses/transaction_detail_modal.html',
                {
                    'transaction': transaction,
                    'form': form,
                    'currency_code': currency_code,
                    'currency_symbol': currency_symbol,
                },
                request=request,
            )
            return HttpResponse(html, status=400)
    else:
        form = TransactionForm(
            instance=transaction,
            currency_code=currency_code,
        )

    if ajax:
        html = render_to_string(
            'expenses/transaction_detail_modal.html',
            {
                'transaction': transaction,
                'form': form,
                'currency_code': currency_code,
                'currency_symbol': currency_symbol,
            },
            request=request,
        )
        return HttpResponse(html)

    return render(
        request,
        'expenses/transaction_detail.html',
        {
            'transaction': transaction,
            'form': form,
            'currency_code': currency_code,
            'currency_symbol': currency_symbol,
        },
    )


@login_required
def transaction_delete(request, pk):
    """Ask for confirmation before deleting a transaction."""

    transaction = get_object_or_404(
        Transaction, pk=pk, user=request.user
    )
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    currency_symbol = get_currency_symbol(currency_code)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('dashboard')

    return render(
        request,
        'expenses/transaction_confirm_delete.html',
        {
            'transaction': transaction,
            'currency_code': currency_code,
            'currency_symbol': currency_symbol,
        },
    )


def custom_logout(request):
    """Log the user out and send them back to the login page."""

    logout(request)
    return redirect('account_login')


@login_required
def delete_account(request):
    """Ask for confirmation, then delete the user's account."""

    if request.method == 'POST':
        user = request.user
        username = user.username
        # Log the session out first so related auth data clears cleanly.
        logout(request)
        user.delete()
        return render(
            request,
            'account/delete_success.html',
            {'username': username},
        )

    return render(request, 'account/delete_account.html')


@login_required
def clear_history(request):
    """Provide a confirmation screen before wiping transaction history."""

    transaction_count = Transaction.objects.filter(user=request.user).count()

    if request.method == 'POST':
        Transaction.objects.filter(user=request.user).delete()
        messages.success(
            request,
            'Transaction history cleared. Enjoy the fresh start!'
        )
        return redirect('dashboard')

    return render(
        request,
        'expenses/clear_history_confirm.html',
        {'transaction_count': transaction_count},
    )


@login_required
def transaction_search_results(request):
    """Return rendered search results for the dashboard search column."""

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'html': '', 'count': 0})

    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .order_by('-occurred_on')
    )
    filtered = _filter_transactions(transactions, query)
    search_results = list(filtered[:10])

    html = render_to_string(
        'expenses/search_results_list.html',
        {
            'search_results': search_results,
            'search_query': query,
            'currency_code': currency_code,
        },
        request=request,
    )

    return JsonResponse({
        'html': html,
        'count': len(search_results),
    })


@login_required
def transaction_suggestions(request):
    """Return transaction/category suggestions that match the query."""

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'suggestions': []})

    name_matches = (
        Transaction.objects
        .filter(user=request.user, name__icontains=query)
        .exclude(name='')
        .values_list('name', flat=True)
        .distinct()
        .order_by('name')[:10]
    )
    category_matches = (
        Category.objects
        .filter(is_active=True, name__icontains=query)
        .values_list('name', flat=True)
        .distinct()
        .order_by('name')[:10]
    )

    suggestions = list(dict.fromkeys([*name_matches, *category_matches]))

    return JsonResponse({'suggestions': suggestions})


@login_required
def currency_settings(request):
    """Allow users to update their preferred currency."""

    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = CurrencySettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            updated = form.save()
            display = updated.get_currency_code_display()
            messages.success(request, f"Currency updated to {display}.")
            return redirect('dashboard')
    else:
        form = CurrencySettingsForm(instance=settings_obj)

    return render(
        request,
        'account/currency_settings.html',
        {
            'form': form,
        },
    )
