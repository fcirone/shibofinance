"""Thin wrapper around core.fingerprint for use inside the API."""
from datetime import date

from core.fingerprint import compute_fingerprint


def make_fingerprint(
    instrument_id: str,
    posted_date: date,
    currency: str,
    amount_minor: int,
    description_norm: str,
) -> str:
    return compute_fingerprint(instrument_id, posted_date, currency, amount_minor, description_norm)
