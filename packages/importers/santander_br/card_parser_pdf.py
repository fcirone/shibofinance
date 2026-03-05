"""Santander BR — credit card statement PDF parser.

The card statement PDF is encrypted with the account holder's CPF (11 digits,
no punctuation). Store it as instrument metadata: {"pdf_password": "XXXXXXXXXXX"}.

Structure:
  - Pages 0-1: billing summary (due date, total, payment options)
  - Pages 2+:  "Detalhamento da Fatura"
               CARD_HOLDER - XXXX XXXX XXXX NNNN       ← card section header
               Pagamento e Demais Créditos
               Parcelamentos
               Despesas
               [@ CARD_HOLDER - XXXX XXXX XXXX NNNN]   ← next card (if any)
               Resumo da Fatura                         ← statement totals
"""
import hashlib
import io
import re
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timezone, timedelta

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import CardStatementRow, CardTransactionRow, ImportResult
from importers.santander_br.detector import is_santander_card

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #

# Card section header (with or without leading @):
#   "FABIO LUIZ C SILVA - 5155 XXXX XXXX 0298"
_CARD_HEADER_RE = re.compile(r"@?\s*\S.*?-\s*(\d{4}\s+XXXX\s+XXXX\s+(\d{4}))")

# Transaction date at start of line (DD/MM)
_TX_DATE_RE = re.compile(r"^(?:(\d+)\s+)?(\d{2}/\d{2})\s+(.+)")

# Amount at end of line (handles negative "-14.795,41" and positive "59,90")
_AMOUNT_END_RE = re.compile(r"(-?\d{1,3}(?:\.\d{3})*,\d{2})(?:\s+\S+)?$")

# Installment marker embedded in description: "03/03" or "09/12"
_INSTALLMENT_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\s*$")

# Statement: due date
_VENCIMENTO_RE = re.compile(r"Vencimento\s+(\d{2}/\d{2}/\d{4})")

# Statement: closing date ("compras.*até DD/MM" or "realizados até DD/MM")
_CLOSING_RE = re.compile(r"at[eé]\s+(\d{2}/\d{2})")

# Statement total
_TOTAL_RE = re.compile(r"Saldo Desta Fatura\s+([\d.]+,\d{2})")

# Lines to skip
_SKIP_RE = re.compile(
    r"^(BANCO SANTANDER|Compra\s+Data|Parcela|Pagamento e Demais|"
    r"Parcelamentos$|Despesas$|COTAÇÃO DOLAR|IOF DESPESA|Resumo da Fatura|"
    r"Descrição\s+R\$|Saldo Anterior|Juros|IOF$|\(\+\)|\(-\)|\(=\)|"
    r"Olá,|Esta é|Opções de|Pagamento Total|Parcelamento de Fatura|"
    r"Pagamento Mínimo|ATENCAO|Orientações|Histórico|Posição|Seu Limite|"
    r"Limite Disponível|Limite de|Consulte|Anuidade|ANUIDADE|Cartão Parcela|"
    r"TOTAL\s+R\$|Beneficiária|Agência|Autenticação|Pagável|Vencimento\s*$|"
    r"Beneficiário|Data Documento|Número do Documento|Espécie|Aceite|"
    r"Nosso Número|Uso Banco|Carteira|Quantidade|Instruções|Número do Cartão|"
    r"Pagador|Ficha|Escaneie|Explore|Acesse|Central de Atendimento|"
    r"Consultas|4004|0800|SAC$|Reclamações|Todos|Ouvidoria|Se não|"
    r"Disponível|Santander Way|\d{1,2}/\d+\s+de\s+\d+)",
    re.IGNORECASE,
)

_SECTION_HEADERS = {
    "pagamento e demais créditos",
    "parcelamentos",
    "despesas",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _parse_brl(text: str) -> int | None:
    """Parse a BRL amount string like '1.234,56' or '-59,90' → minor int."""
    m = re.search(r"-?[\d.]+,\d{2}", text)
    if not m:
        return None
    raw = m.group(0).replace(".", "").replace(",", ".")
    try:
        return to_minor(raw)
    except Exception:
        return None


def _parse_date_dm(day_month: str, year: int) -> date:
    day, month = map(int, day_month.split("/"))
    # Handle year rollover: if month > statement month, likely previous year
    return date(year, month, day)


def _extract_statement_info(full_text: str, year: int) -> tuple[date | None, date | None, int, date | None]:
    """Return (statement_start, statement_end, total_minor, due_date)."""
    due_date: date | None = None
    closing_date: date | None = None
    total_minor = 0

    m = _VENCIMENTO_RE.search(full_text)
    if m:
        d, mo, y = map(int, m.group(1).split("/"))
        due_date = date(y, mo, d)
        year = y  # use the due_date year as reference

    m = _CLOSING_RE.search(full_text)
    if m:
        day, month = map(int, m.group(1).split("/"))
        closing_year = year
        if due_date and month > due_date.month:
            closing_year = year - 1
        closing_date = date(closing_year, month, day)

    m = _TOTAL_RE.search(full_text)
    if m:
        total_minor = to_minor(m.group(1).replace(".", "").replace(",", "."))

    statement_end = closing_date or (due_date - timedelta(days=7) if due_date else None)
    statement_start = (statement_end - timedelta(days=31)) if statement_end else None

    return statement_start, statement_end, total_minor, due_date


def _infer_year(tx_month: int, due_date: date | None, ref_year: int) -> int:
    """Infer the full year for a transaction month."""
    if due_date is None:
        return ref_year
    # Transactions near due_date are in due_date.year or due_date.year-1
    if tx_month <= due_date.month:
        return due_date.year
    return due_date.year - 1


# --------------------------------------------------------------------------- #
# Transaction line parser
# --------------------------------------------------------------------------- #

def _parse_tx_line(
    line: str,
    section: str,
    due_date: date | None,
    ref_year: int,
    card_last4: str,
    instrument_id: str,
    credit_card_id: str,
) -> CardTransactionRow | None:
    """Parse a single transaction line into a CardTransactionRow, or None."""
    m = _TX_DATE_RE.match(line)
    if not m:
        return None

    leading_num = int(m.group(1)) if m.group(1) else None
    day_month = m.group(2)
    rest = m.group(3).strip()

    # International lines format: "DESC FOREIGN_AMOUNT CURRENCY_NAME BRL_AMOUNT USD_AMOUNT"
    # e.g. "BROTHAUS 477,01 PESO URUGUAI 68,78 12,14"
    # The BRL amount is the first number AFTER the currency keyword (+ optional word).
    _FOREIGN_CURR_RE = re.compile(
        r"(.+?)\s+\d[\d.,]*\s+(?:PESO|EURO|POUND|FRANC)\w*(?:\s+\w+)?\s+(\d{1,3}(?:\.\d{3})*,\d{2})",
        re.IGNORECASE,
    )
    fc = _FOREIGN_CURR_RE.search(rest)
    if fc:
        amount_str = fc.group(2)   # BRL amount (after currency name)
        desc_raw = fc.group(1).strip()
    else:
        am = _AMOUNT_END_RE.search(rest)
        if not am:
            return None
        amount_str = am.group(1)
        desc_raw = rest[: am.start()].strip()

    # Remove installment marker from description
    installment_total: int | None = None
    installment_number: int | None = None
    inst_m = _INSTALLMENT_RE.search(desc_raw)
    if inst_m:
        installment_number = int(inst_m.group(1))
        installment_total = int(inst_m.group(2))
        desc_raw = desc_raw[: inst_m.start()].strip()

    if not desc_raw:
        return None

    # Derive year from month
    tx_month = int(day_month.split("/")[1])
    tx_year = _infer_year(tx_month, due_date, ref_year)
    tx_day = int(day_month.split("/")[0])
    try:
        posted_date = date(tx_year, tx_month, tx_day)
    except ValueError:
        return None

    amount_minor = _parse_brl(amount_str)
    if amount_minor is None:
        return None

    # Payments are negative (credits), expenses positive (debits for card)
    if section == "pagamento e demais créditos":
        # negative means credit back to card; keep sign as-is
        pass
    else:
        amount_minor = abs(amount_minor)

    desc_norm = normalize_description(desc_raw)
    fp = compute_fingerprint(instrument_id, posted_date, "BRL", amount_minor, desc_norm)
    posted_at = datetime(posted_date.year, posted_date.month, posted_date.day, 12, 0, 0, tzinfo=timezone.utc)

    return CardTransactionRow(
        posted_at=posted_at,
        posted_date=posted_date,
        description_raw=desc_raw,
        description_norm=desc_norm,
        merchant_raw=desc_raw,
        amount_minor=amount_minor,
        currency="BRL",
        installments_total=installment_total,
        installment_number=installment_number,
        source_tx_id=None,
        fingerprint_hash=fp,
        raw_payload={
            "section": section,
            "raw_line": line,
            "leading_num": leading_num,
        },
    )


# --------------------------------------------------------------------------- #
# Main parse
# --------------------------------------------------------------------------- #

def _extract_all_text(reader: pypdf.PdfReader) -> str:
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def parse_card_pdf(
    file_bytes: bytes,
    instrument_id: str,
    instrument_metadata: dict,
) -> ImportResult:
    password = instrument_metadata.get("pdf_password", "")
    last4 = instrument_metadata.get("last4", "")

    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    if reader.is_encrypted:
        if reader.decrypt(password) == 0:
            raise ValueError("Could not decrypt card PDF — check pdf_password in instrument metadata")

    full_text = _extract_all_text(reader)
    lines = full_text.splitlines()

    # Extract statement-level info
    due_date_m = _VENCIMENTO_RE.search(full_text)
    ref_year = int(due_date_m.group(1).split("/")[2]) if due_date_m else datetime.now().year
    statement_start, statement_end, total_minor, due_date = _extract_statement_info(full_text, ref_year)

    transactions: list[CardTransactionRow] = []
    in_detail_section = False
    current_card_last4 = ""
    current_section = ""
    target_card_found = False

    for line in lines:
        stripped = line.strip()

        # Enter detail section
        if not in_detail_section:
            if "Detalhamento da Fatura" in stripped:
                in_detail_section = True
            continue

        # Stop at statement summary
        if "Resumo da Fatura" in stripped:
            break

        # Card section header
        ch = _CARD_HEADER_RE.search(stripped)
        if ch:
            current_card_last4 = ch.group(2)
            current_section = ""
            if not last4 or current_card_last4 == last4:
                target_card_found = True
            else:
                target_card_found = False
            continue

        if not target_card_found:
            continue

        # Section header
        sl = stripped.lower()
        if sl in _SECTION_HEADERS:
            current_section = sl
            continue

        # Skip noise
        if not stripped or _SKIP_RE.match(stripped):
            continue

        # Parse transaction line
        tx = _parse_tx_line(
            stripped,
            current_section,
            due_date,
            ref_year,
            current_card_last4,
            instrument_id,
            instrument_id,
        )
        if tx:
            transactions.append(tx)

    # Disambiguate duplicate fingerprints (e.g. same merchant charged twice same day)
    fp_count: Counter[str] = Counter(tx.fingerprint_hash for tx in transactions)
    occurrence: dict[str, int] = {}
    disambiguated: list[CardTransactionRow] = []
    for tx in transactions:
        h = tx.fingerprint_hash
        if fp_count[h] > 1:
            n = occurrence.get(h, 0)
            occurrence[h] = n + 1
            if n > 0:
                new_h = hashlib.sha256(f"{h}|{n}".encode()).hexdigest()
                tx = replace(tx, fingerprint_hash=new_h, raw_payload={**tx.raw_payload, "dup_seq": n})
        disambiguated.append(tx)
    transactions = disambiguated

    statements: list[CardStatementRow] = []
    if statement_start and statement_end:
        statements.append(
            CardStatementRow(
                statement_start=statement_start,
                statement_end=statement_end,
                closing_date=statement_end,
                due_date=due_date,
                total_minor=total_minor,
                currency="BRL",
                raw_payload={"source": "santander_br"},
            )
        )

    return ImportResult(card_transactions=transactions, card_statements=statements)


class SantanderBrCardImporter:
    SOURCE_NAME = "santander_br_card"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        # We can't decrypt without a password at detect time.
        # Return True for any encrypted PDF — refined when BBVA is added.
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            return reader.is_encrypted
        except Exception:
            return False

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        return parse_card_pdf(file_bytes, instrument_id, instrument_metadata or {})
