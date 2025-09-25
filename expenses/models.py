"""Database models for the Ledgerly expenses app."""

from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """User-defined labels applied to transactions (e.g. Groceries)."""

    name = models.CharField(max_length=100)
    # Flag to soft-delete categories without removing historical data.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Single income or outgoing entry recorded by a user."""

    INCOME = 'INCOME'
    OUTGO = 'OUTGO'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (OUTGO, 'Outgoing'),
    ]

    # Owner of the transaction; cascade delete keeps data scoped to user.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    # Optional category to classify the transaction.
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # Direction of money flow.
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    # Store smallest currency unit to avoid floating point rounding.
    amount_in_cents = models.IntegerField()
    # Date the transaction occurred.
    occurred_on = models.DateField()
    # Optional notes for additional context.
    note = models.TextField(blank=True)
    # Auditing timestamps managed automatically by Django.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type}: {self.amount_in_cents} ({self.occurred_on})"
