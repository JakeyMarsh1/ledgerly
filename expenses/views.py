"""All of my Ledgerly expense views live together in this module."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Tuple

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils import timezone

from .currencies import (
    DEFAULT_CURRENCY,
    MAX_CENTS,
    cents_to_display,
    get_currency_symbol,
    parse_display_amount_to_cents,
)
from .forms import CurrencySettingsForm, TransactionForm
from .models import Category, Transaction, UserSettings


def _is_ajax(request) -> bool:
    """Return ``True`` when I can tell the request came from AJAX."""

    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _filter_transactions(queryset, search_query):
    """
    Filter transactions by search term across:
    - Transaction name/description
    - Category name
    - Transaction type
    - Note field content
    Returns filtered queryset with case-insensitive matching
    """

    if not search_query:
        return queryset

    return queryset.filter(
        Q(note__icontains=search_query)
        | Q(category__name__icontains=search_query)
        | Q(type__icontains=search_query)
        | Q(name__icontains=search_query)
    )


def _cycle_month_shift(reference: date, months: int, cycle_day: int) -> date:
    """Shift a reference date by whole months while keeping my cycle day."""

    year = reference.year + (reference.month - 1 + months) // 12
    month = (reference.month - 1 + months) % 12 + 1
    day = min(cycle_day, monthrange(year, month)[1])
    return date(year, month, day)


def _user_transactions(user) -> models.QuerySet:
    """Return the transaction queryset I scope to the incoming user."""

    return Transaction.objects.filter(user=user)


def _get_user_settings_details(user) -> Tuple[UserSettings, str, str]:
    """Fetch my user settings record plus the resolved currency details."""

    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    currency_code = settings_obj.currency_code or DEFAULT_CURRENCY
    currency_symbol = get_currency_symbol(currency_code)
    return settings_obj, currency_code, currency_symbol


def _max_transaction_amount_display() -> str:
    """Return the largest transaction amount I allow, formatted for display."""

    return str((Decimal(MAX_CENTS) / Decimal(100)).quantize(Decimal('0.00')))


@login_required
def dashboard(request):
    """
    Main dashboard view showing monthly financial summary with:
    - Income vs expense breakdown for current month
    - Recent transactions list (last 15)
    - Chart data for last 12 cycles
    - Quick-add transaction modals
    - Search functionality
    """

    # I only surface active categories so I can tag transactions cleanly.
    categories = Category.objects.filter(is_active=True)

    # I pull the user's configuration, including their cycle anchor day.
    settings_obj, currency_code, currency_symbol = _get_user_settings_details(
        request.user
    )

    # I always scope transactions to the signed-in user.
    transactions = _user_transactions(request.user).order_by('-occurred_on')

    # I calculate cycle-aware stats using the user's configured start day.
    today = timezone.localdate()
    cycle_day = (
        settings_obj.cycle_start_date.day
        if settings_obj.cycle_start_date
        else 1
    )
    cycle_candidate = _cycle_month_shift(today, 0, cycle_day)
    if cycle_candidate > today:
        current_cycle_start = _cycle_month_shift(today, -1, cycle_day)
    else:
        current_cycle_start = cycle_candidate
    next_cycle_start = _cycle_month_shift(current_cycle_start, 1, cycle_day)
    current_cycle_end = next_cycle_start - timedelta(days=1)

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

    # I let the dashboard search box filter transactions on the fly.
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
    total_flow = income + outgo
    if total_flow > 0:
        income_percent = round((income / total_flow) * 100, 2)
        expense_percent = round((outgo / total_flow) * 100, 2)
    else:
        income_percent = 0
        expense_percent = 0

    top_spend = (
        cycle_transactions
        .filter(type='OUTGO')
        .order_by('-amount_in_cents')
        .first()
    )

    # I build cycle labels and totals for the past 12 cycles
    # (oldest -> newest).
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
        # I figure out which inline modal kicked off the submission.
        action = request.POST.get('action', 'add_transaction')

        if action == 'update_cycle_start':
            cycle_start_raw = request.POST.get('cycle_start_date')
            if cycle_start_raw:
                try:
                    cycle_start_date = date.fromisoformat(cycle_start_raw)
                except ValueError:
                    messages.error(
                        request,
                        'Please provide a valid cycle start date.',
                    )
                    return redirect('dashboard')

                # I store the user's preferred cycle anchor day so future
                # queries stay aligned with their reporting window.
                settings_obj.cycle_start_date = cycle_start_date
                settings_obj.save(update_fields=['cycle_start_date'])
                messages.success(
                    request,
                    'Cycle start updated successfully.'
                )
            return redirect('dashboard')

        # Otherwise I persist the new transaction from the submitted form.
        # I still allow missing categories and store them as NULL for
        # flexibility.
        transaction_type = (request.POST.get('type') or '').upper()
        if transaction_type not in {'INCOME', 'OUTGO'}:
            messages.error(
                request,
                'Please choose whether this entry is income or an expense.',
            )
            return redirect('dashboard')

        category_id = request.POST.get('category') or None
        if transaction_type == 'OUTGO' and category_id is None:
            messages.error(
                request,
                'Outgoing transactions require a category. '
                'Please choose one before saving.',
            )
            return redirect('dashboard')

        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Please enter a name for the transaction.')
            return redirect('dashboard')

        occurred_on_raw = request.POST.get('occurred_on')
        try:
            occurred_on = date.fromisoformat(occurred_on_raw)
        except (TypeError, ValueError):
            messages.error(
                request,
                'Please select a valid date before saving the transaction.',
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
            name=name,
            type=transaction_type,
            amount_in_cents=amount_cents,
            category_id=category_id,
            occurred_on=occurred_on,
            note=request.POST.get('note', ''),
        )
        success_messages = {
            'INCOME': 'Income saved successfully.',
            'OUTGO': 'Expense saved successfully.',
        }
        messages.success(request, success_messages[transaction_type])
        return redirect('dashboard')

    context = {
        # I pass the full category list to the form.
        'categories': categories,
        # I show the 10 most recent transactions on the dashboard.
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
        'cycle_display_end': current_cycle_end,
        'cycle_setting_start': settings_obj.cycle_start_date,
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
        'max_transaction_amount': _max_transaction_amount_display(),
        'income_percent': income_percent,
        'expense_percent': expense_percent,
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def transaction_list(request):
    """I show the full history of the signed-in user's transactions."""

    transactions = _user_transactions(request.user).order_by('-occurred_on')
    _, currency_code, currency_symbol = _get_user_settings_details(
        request.user
    )
    return render(request, 'expenses/transaction_list.html', {
        'transactions': transactions,
        'currency_code': currency_code,
        'currency_symbol': currency_symbol,
    })


@login_required
def transaction_detail(request, pk):
    """I display and let the user edit a single transaction."""

    transaction = get_object_or_404(
        Transaction, pk=pk, user=request.user
    )

    ajax = _is_ajax(request)
    _, currency_code, currency_symbol = _get_user_settings_details(
        request.user
    )

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
    """I ask for confirmation before removing a transaction."""

    transaction = get_object_or_404(
        Transaction, pk=pk, user=request.user
    )
    _, currency_code, currency_symbol = _get_user_settings_details(
        request.user
    )

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


@login_required
def transaction_calendar_data(request):
    """I return month-level transaction details for the calendar modal."""

    today = timezone.localdate()
    year_param = request.GET.get('year')
    month_param = request.GET.get('month')

    try:
        year = int(year_param) if year_param else today.year
    except (TypeError, ValueError):
        year = today.year

    try:
        month = int(month_param) if month_param else today.month
    except (TypeError, ValueError):
        month = today.month

    if month < 1 or month > 12:
        month = today.month

    if year < 1900 or year > today.year + 5:
        year = today.year

    try:
        start_date = date(year, month, 1)
    except ValueError:
        start_date = date(today.year, today.month, 1)
        year = start_date.year
        month = start_date.month

    days_in_month = monthrange(year, month)[1]
    end_date = date(year, month, days_in_month)
    next_month = end_date + timedelta(days=1)

    _, currency_code, currency_symbol = _get_user_settings_details(
        request.user
    )

    month_transactions = (
        _user_transactions(request.user)
        .filter(
            occurred_on__gte=start_date,
            occurred_on__lt=next_month,
        )
        .select_related('category')
        .order_by('occurred_on', 'name', 'pk')
    )

    type_labels = dict(Transaction.TYPE_CHOICES)
    day_map = {}
    for txn in month_transactions:
        day_key = txn.occurred_on.isoformat()
        day_map.setdefault(day_key, []).append({
            'id': txn.pk,
            'name': txn.name,
            'type': txn.type,
            'type_display': type_labels.get(txn.type, txn.type.title()),
            'category': txn.category.name if txn.category else 'Uncategorized',
            'note': txn.note or '',
            'amount_display': (
                f"-{cents_to_display(txn.amount_in_cents, currency_code)}"
                if txn.type == Transaction.OUTGO
                else f"+{cents_to_display(txn.amount_in_cents, currency_code)}"
            ),
            'detail_url': reverse('transaction_detail', args=[txn.pk]),
            'occurred_on': txn.occurred_on.isoformat(),
        })

    days = [
        {'date': day, 'transactions': entries}
        for day, entries in sorted(day_map.items())
    ]

    month_prefix = f"{year:04d}-{month:02d}"
    today_iso = today.isoformat()

    if today_iso.startswith(month_prefix):
        initial_date = today_iso
    elif days:
        initial_date = days[0]['date']
    else:
        initial_date = start_date.isoformat()

    return JsonResponse({
        'year': year,
        'month': month,
        'month_label': start_date.strftime('%B %Y'),
        'days': days,
        'currency_symbol': currency_symbol,
        'today': today_iso,
        'initial_date': initial_date,
    })


def custom_logout(request):
    """I log the user out and send them back to the login page."""

    logout(request)
    return redirect('account_login')


@login_required
def delete_account(request):
    """I ask for confirmation and then delete the user's account."""

    if request.method == 'POST':
        user = request.user
        username = user.username
    # I log the session out first so the auth data clears cleanly.
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
    """I provide a confirmation screen before wiping transaction history."""

    user_transactions = _user_transactions(request.user)
    transaction_count = user_transactions.count()

    if request.method == 'POST':
        user_transactions.delete()
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
    """I return rendered search results for the dashboard search column."""

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'html': '', 'count': 0})

    _, currency_code, _ = _get_user_settings_details(request.user)
    transactions = _user_transactions(request.user).order_by('-occurred_on')
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
    """I return transaction or category suggestions that match the query."""

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'suggestions': []})

    name_matches = (
        _user_transactions(request.user)
        .filter(name__icontains=query)
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
    """I let users update their preferred currency."""

    settings_obj, _, _ = _get_user_settings_details(request.user)
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
