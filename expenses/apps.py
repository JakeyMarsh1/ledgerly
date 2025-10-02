"""I configure the Ledgerly expenses app."""

from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    """I let Django know how to bootstrap the expenses app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expenses'
