"""Integer minor-unit conversion helpers.

All monetary values are stored as signed integers in minor units.
Example: 100.50 BRL -> 10050, -3.99 USD -> -399
"""
from decimal import ROUND_HALF_UP, Decimal


def to_minor(amount: str | float | Decimal, decimals: int = 2) -> int:
    """Convert a decimal amount to integer minor units."""
    factor = Decimal(10) ** decimals
    return int((Decimal(str(amount)) * factor).to_integral_value(ROUND_HALF_UP))


def from_minor(amount_minor: int, decimals: int = 2) -> Decimal:
    """Convert integer minor units back to a Decimal."""
    factor = Decimal(10) ** decimals
    return Decimal(amount_minor) / factor
