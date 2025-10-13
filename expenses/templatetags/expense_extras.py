"""Custom template filters for Ledgerly templates."""

from django import template

from expenses.models import Transaction

register = template.Library()


@register.filter(name="cents_to_currency")
def cents_to_currency(value, currency_code="USD"):
    """Convert an integer amount in cents to a formatted currency string."""

    from expenses.currencies import cents_to_display  # avoid circular import

    try:
        cents_value = int(value)
    except (TypeError, ValueError):
        cents_value = 0

    return cents_to_display(cents_value, currency_code)


@register.filter(name="display_category")
def display_category(transaction):
    """Return a human-readable category label, forcing income to show N/A."""

    if not transaction:
        return "N/A"

    txn_type = getattr(transaction, "type", None)
    if txn_type == Transaction.INCOME:
        return "N/A"

    category = getattr(transaction, "category", None)
    if category:
        return str(category)

    return "N/A"
