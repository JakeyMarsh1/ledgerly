"""Views powering Ledgerly's expense tracking experience."""

from calendar import monthrange
from datetime import date

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Sum
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import Category, Transaction, UserSettings


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
    filtered_transactions = transactions
    if search_query:
        filtered_transactions = filtered_transactions.filter(
            Q(note__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(type__icontains=search_query)
        )

    display_transactions = cycle_transactions
    if search_query:
        display_transactions = filtered_transactions
    display_transactions = display_transactions[:10]
    top_expenses = (
        cycle_transactions
        .filter(type='OUTGO')
        .order_by('-amount_in_cents')[:5]
    )
    outgo = (
        cycle_transactions
        .filter(type='OUTGO')
        .aggregate(total=models.Sum('amount_in_cents'))['total']
        or 0
    )
    balance = income - outgo

    # Most expensive spend for the current month (None when no data yet).
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
        start.strftime('Cycle starting %d %b %Y')
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
        Transaction.objects.create(
            user=request.user,
            type=request.POST['type'],
            amount_in_cents=request.POST['amount_in_cents'],
            category_id=request.POST.get('category') or None,
            occurred_on=request.POST['occurred_on'],
            note=request.POST.get('note', ''),
        )
        return redirect('dashboard')

    context = {
        # Pass full category list to the form.
        'categories': categories,
        # Show the 10 most recent transactions on the dashboard.
        'transactions': display_transactions,
        'income': income,
        'outgo': outgo,
        'balance': balance,
        'top_spend': top_spend,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data,
        'search_query': search_query,
        'top_expenses': top_expenses,
        'cycle_display_start': current_cycle_start,
        'cycle_setting_start': settings_obj.cycle_start_date,
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
    return render(request, 'expenses/transaction_list.html', {
        'transactions': transactions,
    })


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

