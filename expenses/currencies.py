"""Currency helpers and metadata for Ledgerly."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Tuple

CURRENCY_CHOICES: Iterable[Tuple[str, str]] = (
    ("USD", "US Dollar ($)"),
    ("GBP", "British Pound (£)"),
    ("EUR", "Euro (€)"),
)

DEFAULT_CURRENCY = "USD"

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "GBP": "£",
    "EUR": "€",
}

MAX_CENTS = 9_000_000_000_000_00  # 9 trillion in cents/pence.


def get_currency_symbol(code: str) -> str:
    """Return the symbol for the supplied ISO currency code."""

    return CURRENCY_SYMBOLS.get(code, CURRENCY_SYMBOLS[DEFAULT_CURRENCY])


def quantize_amount(value: Decimal) -> Decimal:
    """Round a Decimal value to two places using bankers rounding."""

    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cents_to_display(amount_in_cents: int, currency_code: str) -> str:
    """Format an integer amount of cents in the user's currency."""

    symbol = get_currency_symbol(currency_code)
    try:
        cents = int(amount_in_cents)
    except (TypeError, ValueError):
        cents = 0

    units = Decimal(cents) / Decimal(100)
    formatted = f"{quantize_amount(units):,.2f}"
    return f"{symbol}{formatted}"


def parse_display_amount_to_cents(amount_str: str) -> int:
    """Convert a string amount (e.g. "19.99") into integer cents."""

    value = Decimal(amount_str)
    quantized = quantize_amount(value)
    cents = quantized * Decimal(100)
    return int(cents.to_integral_value(rounding=ROUND_HALF_UP))
