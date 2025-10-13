"""I define the database models for the Ledgerly expenses app."""

from datetime import date

from django.db import models
from django.contrib.auth.models import User

from .currencies import CURRENCY_CHOICES, DEFAULT_CURRENCY


def default_cycle_start():
    """I return the first day of the current month for cycle tracking."""

    today = date.today()
    return today.replace(day=1)


class Category(models.Model):
    """I use user-defined labels to tag transactions (e.g., Groceries)."""

    name = models.CharField(max_length=100)
    # I use this flag to soft-delete categories without losing history.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Catergories'


class Transaction(models.Model):
    """I store a single income or outgoing entry recorded by a user."""

    INCOME = 'INCOME'
    OUTGO = 'OUTGO'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (OUTGO, 'Outgoing'),
    ]

    # I attach each transaction to a user so cascade deletes stay scoped.
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    # I keep an optional category to classify the transaction.
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # I store a short human-readable label for searches and listings.
    name = models.CharField(max_length=120)
    # I track the direction of the money flow.
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    # I store the smallest currency unit to avoid floating point rounding.
    amount_in_cents = models.PositiveBigIntegerField()
    # I capture the date the transaction occurred.
    occurred_on = models.DateField()
    # I keep optional notes for extra context.
    note = models.TextField(blank=True)
    # I let Django manage auditing timestamps automatically.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.name} · {self.type}: {self.amount_in_cents}"
            f" ({self.occurred_on})"
        )


class UserSettings(models.Model):
    """I store per-user configuration like the preferred cycle start date."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings',
    )
    cycle_start_date = models.DateField(default=default_cycle_start)
    currency_code = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=DEFAULT_CURRENCY,
    )

    def __str__(self):
        return f"Settings for {self.user.username}"
