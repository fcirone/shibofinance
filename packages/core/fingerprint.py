"""SHA256 fingerprint for deduplication.

Used when source_tx_id is absent. The hash is derived from:
  instrument_id | posted_date | currency | amount_minor | description_norm
"""
import hashlib
from datetime import date


def compute_fingerprint(
    instrument_id: str,
    posted_date: date,
    currency: str,
    amount_minor: int,
    description_norm: str,
) -> str:
    """Return a hex SHA256 fingerprint for a transaction row."""
    payload = "|".join([
        str(instrument_id),
        posted_date.isoformat(),
        currency,
        str(amount_minor),
        description_norm,
    ])
    return hashlib.sha256(payload.encode()).hexdigest()
