"""BBVA Uruguay — credit card statement PDF parser.

The PDF is NOT encrypted.

Structure:
  - Page 0: statement header + all transactions
  - Page 1: legal disclaimer

Statement header (page 0):
  Cuenta 219612
  Titular FABIO,CIRONE
  Fecha de cierre 26/02/2026     ← closing_date
  Vencimiento actual 12/03/2026  ← due_date
  Total a pagar 19,091.85 29.99  ← total_minor (UYU pesos)

Column header:
  Fecha Descripción Pesos Dólares

Transaction line format:
  DD/MM/YYYY  DESCRIPTION  [N/M]  PESOS  DOLLARS

Examples:
  11/02/2026 MAPFRE 340.23 0.00
  09/05/2025 MERPAGO*TODOGASTROSAS 10/10 1,029.42 0.00
  01/02/2026 DISNEY PLUS (US ,USD, 29,99) 0.00 29.99

Lines to skip:
  SALDO ANTERIOR, SU PAGO (negative = payment), SALDO PENDIENTE,
  SALDO CONTADO, Total a pagar, Pago mínimo, TARJETA XXXX - NAME,
  SEGURO VIDA (fee without date — no reliable date to attach),
  negative amounts (credits/reversals), legal disclaimer lines.

Number format:
  Comma = thousands separator, dot = decimal  (US style)
  e.g. 1,029.42  or  35,457.76

Currency:
  Primary = UYU (Pesos column); also stores USD amount in raw_payload.
  If Pesos amount is 0 and USD > 0, currency is USD.
"""
import io
import re
from datetime import date, datetime, timedelta, timezone

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import CardStatementRow, CardTransactionRow, ImportResult
from importers.bbva_uy.detector import is_bbva_card

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

_CLOSING_RE = re.compile(r"Fecha\s+de\s+cierre\s+(\d{2}/\d{2}/\d{4})")
_DUE_RE = re.compile(r"Vencimiento\s+actual\s+(\d{2}/\d{2}/\d{4})")
_TOTAL_RE = re.compile(r"Total\s+a\s+pagar\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})")

# Transaction: DD/MM/YYYY  DESCRIPTION  [N/M]  PESOS  DOLLARS
_TX_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+"        # date
    r"(.*?)\s+"                         # description
    r"(?:(\d{1,2}/\d{1,2})\s+)?"       # optional installment N/M
    r"(-?[\d,]+\.\d{2})\s+"            # pesos amount
    r"(-?[\d,]+\.\d{2})\s*$"           # dollars amount
)

# Cardholder section header: "TARJETA 4016 - FABIO,CIRONE"
_CARDHOLDER_RE = re.compile(r"^TARJETA\s+\d{4}\s+-\s+", re.IGNORECASE)

_SKIP_RE = re.compile(
    r"^(SALDO\s+(ANTERIOR|PENDIENTE|CONTADO)|SU\s+PAGO|"
    r"Total\s+a\s+pagar|Pago\s+m[ií]nimo|SEGURO|Tasas|"
    r"Financiaci[oó]n|Mora|\(\*\)|C[oó]mo\s+se|Quienes|"
    r"Cuenta\s+\d|Titular\s+|Domicilio|Fecha\s+de\s+cierre|"
    r"Vencimiento|Pr[oó]xim|Fecha\s+Descripci|"
    r"Reclamos|BBVA|casilla|podr[aá]n|En\s+caso|También|"
    r"uy\s*$)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    """Parse DD/MM/YYYY."""
    d, m, y = s.split("/")
    return date(int(y), int(m), int(d))


def _parse_us_amount(s: str) -> int:
    """Parse US-format number (1,029.42) to minor units."""
    return to_minor(s.replace(",", ""))


def _extract_statement_info(full_text: str) -> tuple[date, date, date | None, int]:
    """Return (statement_start, statement_end/closing, due_date, total_minor)."""
    closing_date: date | None = None
    due_date: date | None = None
    total_minor = 0

    m = _CLOSING_RE.search(full_text)
    if m:
        closing_date = _parse_date(m.group(1))

    m = _DUE_RE.search(full_text)
    if m:
        due_date = _parse_date(m.group(1))

    m = _TOTAL_RE.search(full_text)
    if m:
        total_minor = _parse_us_amount(m.group(1))  # UYU pesos

    if closing_date is None and due_date is not None:
        closing_date = due_date - timedelta(days=17)  # heuristic

    if closing_date is None:
        closing_date = date.today()

    statement_end = closing_date
    statement_start = closing_date - timedelta(days=35)  # approximation

    return statement_start, statement_end, due_date, total_minor


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_transactions(
    lines: list[str],
    credit_card_id: str,
    closing_date: date,
) -> list[CardTransactionRow]:
    from collections import Counter

    rows: list[CardTransactionRow] = []
    seen_fps: Counter = Counter()
    in_tx_section = False

    for raw in lines:
        line = re.sub(r" {2,}", " ", raw).strip()

        if not line:
            continue

        # Detect start of transaction table
        if re.match(r"^Fecha\s+Descripci", line, re.IGNORECASE):
            in_tx_section = True
            continue

        if not in_tx_section:
            continue

        # Skip cardholder section header
        if _CARDHOLDER_RE.match(line):
            continue

        if _SKIP_RE.match(line):
            continue

        m = _TX_RE.match(line)
        if not m:
            continue

        date_str = m.group(1)
        desc_raw = m.group(2).strip()
        installment_str = m.group(3)
        pesos_str = m.group(4)
        dollars_str = m.group(5)

        pesos_amount = _parse_us_amount(pesos_str)
        dollars_amount = _parse_us_amount(dollars_str)

        # Skip payments/credits (negative amounts)
        if pesos_amount < 0 or dollars_amount < 0:
            continue

        # Determine primary currency and amount
        if pesos_amount > 0:
            amount_minor = pesos_amount
            currency = "UYU"
        elif dollars_amount > 0:
            amount_minor = dollars_amount
            currency = "USD"
        else:
            continue  # zero on both

        if amount_minor <= 0:
            continue

        # Parse installment
        installment_number: int | None = None
        installments_total: int | None = None
        if installment_str:
            parts = installment_str.split("/")
            installment_number = int(parts[0])
            installments_total = int(parts[1])

        posted_date = _parse_date(date_str)
        desc_norm = normalize_description(desc_raw)
        fp = compute_fingerprint(credit_card_id, posted_date, currency, amount_minor, desc_norm)

        seen_fps[fp] += 1
        if seen_fps[fp] > 1:
            fp = compute_fingerprint(
                credit_card_id, posted_date, currency, amount_minor,
                f"{desc_norm} #{seen_fps[fp]}",
            )

        posted_at = datetime(
            posted_date.year, posted_date.month, posted_date.day, 12, 0, 0,
            tzinfo=timezone.utc,
        )

        rows.append(
            CardTransactionRow(
                posted_at=posted_at,
                posted_date=posted_date,
                description_raw=desc_raw,
                description_norm=desc_norm,
                merchant_raw=None,
                amount_minor=amount_minor,
                currency=currency,
                installments_total=installments_total,
                installment_number=installment_number,
                source_tx_id=None,
                fingerprint_hash=fp,
                raw_payload={
                    "raw": desc_raw,
                    "pesos": pesos_str,
                    "dollars": dollars_str,
                },
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------

class BbvaUyCardImporter:
    SOURCE_NAME = "bbva_uy_card"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        return is_bbva_card(file_bytes)

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        lines = full_text.splitlines()

        statement_start, statement_end, due_date, total_minor = _extract_statement_info(full_text)

        txs = _parse_transactions(lines, instrument_id, statement_end)

        statement = CardStatementRow(
            statement_start=statement_start,
            statement_end=statement_end,
            closing_date=statement_end,
            due_date=due_date,
            total_minor=total_minor,
            currency="UYU",
            raw_payload={
                "due_date": str(due_date),
                "closing_date": str(statement_end),
                "total_minor": total_minor,
            },
        )

        return ImportResult(card_transactions=txs, card_statements=[statement])
