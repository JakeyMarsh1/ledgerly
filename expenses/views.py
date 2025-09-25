from django.utils import timezone
from .models import Category, Transaction
from django.shortcuts import render, redirect
from django.db import models


def dashboard(request):
    categories = Category.objects.filter(is_active=True)
    transactions = Transaction.objects.filter(user=request.user).order_by('-occurred_on')

    # Calculate monthly stats
    now = timezone.now()
    month_transactions = transactions.filter(occurred_on__year=now.year, occurred_on__month=now.month)
    income = month_transactions.filter(type='INCOME').aggregate(total=models.Sum('amount_in_cents'))['total'] or 0
    outgo = month_transactions.filter(type='OUTGO').aggregate(total=models.Sum('amount_in_cents'))['total'] or 0
    balance = income - outgo

    # Most expensive spend
    top_spend = month_transactions.filter(type='OUTGO').order_by('-amount_in_cents').first()

    if request.method == 'POST':
        Transaction.objects.create(
            user=request.user,
            type=request.POST['type'],
            amount_in_cents=request.POST['amount_in_cents'],
            category_id=request.POST.get('category') or None,
            occurred_on=request.POST['occurred_on'],
            note=request.POST.get('note', '')
        )
        return redirect('dashboard')

    context = {
        'categories': categories,
        'transactions': transactions[:10],  # Show recent 10
        'income': income,
        'outgo': outgo,
        'balance': balance,
        'top_spend': top_spend,
    }
    return render(request, 'expenses/dashboard.html', context)


def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-occurred_on')
    return render(request, 'expenses/transaction_list.html', {'transactions': transactions})
