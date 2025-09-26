"""Application configuration for the Ledgerly expenses app."""

from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    """Ensure Django knows how to bootstrap the expenses app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expenses'
