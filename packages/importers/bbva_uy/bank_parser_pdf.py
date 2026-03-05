"""BBVA Uruguay — bank statement PDF parser.

The PDF is encrypted with an empty password (owner-password-only encryption).

Structure:
  - Multiple pages, each starting with account holder header
  - One or more currency sections per document:
      "PESOS URUGUAYOS"  → currency UYU
      "DOLARES U.S.A."   → currency USD

Column header line (repeated on each page per section):
  Fecha   Descripcion   Fecha Valor   Debito   Haber   Saldo

Transaction line format:
  D/MM/YY   DESCRIPTION   [D/MM/YY]   AMOUNT   SALDO

Notes:
  - All amounts use European format: dot=thousands, comma=decimal
  - The "Fecha Valor" (value date) column is optional; some lines include it
  - There is no debit/credit sign in the text; sign is determined by comparing
    AMOUNT with the change in SALDO:
      prev_saldo + AMOUNT ≈ SALDO  → credit (positive)
      prev_saldo - AMOUNT ≈ SALDO  → debit  (negative)
  - Initial saldo line: just date + one number (opening balance; skip)
  - "PROMEDIO MENSUAL" lines are footers; skip
"""
import io
import re
from datetime import date, datetime, timezone

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import BankTransactionRow, ImportResult
from importers.bbva_uy.detector import is_bbva_bank

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Section currency header
_UYU_RE = re.compile(r"PESOS\s+URUGUAYOS", re.IGNORECASE)
_USD_RE = re.compile(r"DOLARES\s+U\.S\.A\.", re.IGNORECASE)

# Column header line
_HEADER_RE = re.compile(r"Fecha\s+Descripcion\s+Fecha\s+Valor", re.IGNORECASE)

# Opening balance line: only date + one amount (no second amount)
# e.g. "  30/11/25    14.168,11"
_OPENING_RE = re.compile(
    r"^\s*(\d{1,2}/\d{2}/\d{2})\s+([\d.]+,\d{2})\s*$"
)

# Full transaction line: date + description + optional_fecha_valor + amount + saldo
# Amount and saldo are the two trailing European-format numbers.
_TX_RE = re.compile(
    r"^\s*(\d{1,2}/\d{2}/\d{2})\s+"    # transaction date
    r"(.*?)\s+"                           # description (may include fecha valor)
    r"([\d.]+,\d{2})\s+"                 # transaction amount
    r"([\d.]+,\d{2})\s*$"                # saldo
)

# Optional fecha valor at end of description: D/MM/YY
_FECHA_VALOR_RE = re.compile(r"\s+(\d{1,2}/\d{2}/\d{2})\s*$")

# Lines to skip unconditionally
_SKIP_RE = re.compile(
    r"^(CIRONE|RUTA|MONTEVIDEO|Fecha\s*:|Per[ií]odo|P[áa]gina|Cuenta\s*:|"
    r"PROMEDIO|Rogamos|Acumulado|BBVA|También|casilla|podr[áa]n|"
    r"posibilidad|Reclamos|comunica|Asimismo|s\s+\d|j:|577|2026\d|"
    r"Banca:|Ejecutivo:|Titular:)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_eu_amount(s: str) -> int:
    """Parse European-format number (1.234,56) to minor units."""
    return to_minor(s.replace(".", "").replace(",", "."))


def _parse_date(s: str) -> date:
    """Parse D/MM/YY to date."""
    parts = s.split("/")
    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
    if y < 100:
        y += 2000
    return date(y, m, d)


def _clean_desc(desc: str) -> str:
    """Remove optional fecha-valor suffix from description."""
    return _FECHA_VALOR_RE.sub("", desc).strip()


def _determine_sign(amount: int, saldo: int, prev_saldo: int) -> int | None:
    """Return +1 (credit) or -1 (debit), or None if undetermined."""
    if abs(prev_saldo + amount - saldo) <= 1:
        return 1
    if abs(prev_saldo - amount - saldo) <= 1:
        return -1
    return None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_section(
    lines: list[str],
    currency: str,
    instrument_id: str,
) -> list[BankTransactionRow]:
    from collections import Counter
    rows: list[BankTransactionRow] = []
    seen_fps: Counter = Counter()
    prev_saldo: int | None = None
    in_tx_section = False

    for raw in lines:
        line = re.sub(r" {2,}", " ", raw).strip()

        if not line:
            continue

        # Detect column header → start of transactions
        if _HEADER_RE.search(line):
            in_tx_section = True
            continue

        if not in_tx_section:
            continue

        if _SKIP_RE.match(line):
            continue

        # Opening balance line (only one amount at end)
        m = _OPENING_RE.match(line)
        if m:
            prev_saldo = _parse_eu_amount(m.group(2))
            continue

        # Full transaction line (two amounts at end)
        m = _TX_RE.match(line)
        if not m:
            continue

        date_str = m.group(1)
        desc_raw = _clean_desc(m.group(2))
        amount = _parse_eu_amount(m.group(3))
        saldo = _parse_eu_amount(m.group(4))

        if not desc_raw:
            prev_saldo = saldo
            continue

        sign = None
        if prev_saldo is not None:
            sign = _determine_sign(amount, saldo, prev_saldo)

        prev_saldo = saldo

        if sign is None:
            # Cannot determine direction; skip (edge case on first line)
            continue

        signed = sign * amount
        posted_date = _parse_date(date_str)
        desc_norm = normalize_description(desc_raw)
        fp = compute_fingerprint(instrument_id, posted_date, currency, signed, desc_norm)
        seen_fps[fp] += 1
        if seen_fps[fp] > 1:
            fp = compute_fingerprint(
                instrument_id, posted_date, currency, signed,
                f"{desc_norm} #{seen_fps[fp]}",
            )
        posted_at = datetime(
            posted_date.year, posted_date.month, posted_date.day, 12, 0, 0,
            tzinfo=timezone.utc,
        )

        rows.append(
            BankTransactionRow(
                posted_at=posted_at,
                posted_date=posted_date,
                description_raw=desc_raw,
                description_norm=desc_norm,
                amount_minor=signed,
                currency=currency,
                source_tx_id=None,
                fingerprint_hash=fp,
                raw_payload={"raw": raw.strip()},
            )
        )

    return rows


def _split_currency_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split lines into (currency, lines) sections.

    The currency header line repeats on every page, so we accumulate all lines
    for the same currency into a single list (order preserved).
    """
    sections: dict[str, list[str]] = {}
    currency_order: list[str] = []
    current_currency: str | None = None

    for line in lines:
        if _UYU_RE.search(line):
            current_currency = "UYU"
            if "UYU" not in sections:
                sections["UYU"] = []
                currency_order.append("UYU")
        elif _USD_RE.search(line):
            current_currency = "USD"
            if "USD" not in sections:
                sections["USD"] = []
                currency_order.append("USD")
        elif current_currency is not None:
            sections[current_currency].append(line)

    return [(c, sections[c]) for c in currency_order]


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------

class BbvaUyBankImporter:
    SOURCE_NAME = "bbva_uy_bank"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        return is_bbva_bank(file_bytes)

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            reader.decrypt("")

        lines: list[str] = []
        for page in reader.pages:
            lines.extend((page.extract_text() or "").splitlines())

        sections = _split_currency_sections(lines)
        txs: list[BankTransactionRow] = []
        for currency, section_lines in sections:
            txs.extend(_parse_section(section_lines, currency, instrument_id))

        return ImportResult(bank_transactions=txs)
