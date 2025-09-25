"""Views powering Ledgerly's expense tracking experience."""

from django.utils import timezone
from .models import Category, Transaction
from django.shortcuts import render, redirect
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


@login_required
def dashboard(request):
    """Render the main dashboard with transaction form and monthly stats."""

    # Only show active categories so users can classify transactions.
    categories = Category.objects.filter(is_active=True)

    # Limit transactions to the logged-in user for data isolation.
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .order_by('-occurred_on')
    )

    # Calculate monthly stats
    now = timezone.now()
    month_transactions = transactions.filter(
        occurred_on__year=now.year,
        occurred_on__month=now.month,
    )
    income = (
        month_transactions
        .filter(type='INCOME')
        .aggregate(total=models.Sum('amount_in_cents'))['total']
        or 0
    )
    outgo = (
        month_transactions
        .filter(type='OUTGO')
        .aggregate(total=models.Sum('amount_in_cents'))['total']
        or 0
    )
    balance = income - outgo

    # Most expensive spend for the current month (None when no data yet).
    top_spend = (
        month_transactions
        .filter(type='OUTGO')
        .order_by('-amount_in_cents')
        .first()
    )

    if request.method == 'POST':
        # Persist the new transaction straight from the submitted form.
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
        'transactions': transactions[:10],
        'income': income,
        'outgo': outgo,
        'balance': balance,
        'top_spend': top_spend,
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
