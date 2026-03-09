"""Santander BR — bank statement PDF parser.

The Santander "Extrato Consolidado Inteligente" PDF is unencrypted.
Transaction section layout (each row can span 1-3 lines):

    DD/MM  DESCRIPTION - AMOUNT[-]          ← single-line tx
    DD/MM  DESCRIPTION                       ← multi-line tx start
    DESCRIPTION_CONT                         ← continuation
    - AMOUNT[-]                              ← amount-only line
     DESCRIPTION - AMOUNT[-]                ← same-date next tx (leading space)

A trailing '-' after the amount means debit; otherwise credit.
"""
import io
import re
from datetime import date, datetime, timezone

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import BankTransactionRow, ImportResult
from importers.santander_br.detector import is_santander_bank

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #

# New-date line: DD/MM followed by 2+ spaces
_DATE_RE = re.compile(r"^(\d{2}/\d{2})\s{2,}(.*)")

# Amount at end of line, two formats:
#   "- NNN,NN[-]"          — no document number (leading dash is separator)
#   "DDDDDD NNN,NN[-]"     — 5-6 digit document number precedes amount
# Optionally followed by a balance column (which may itself end with "-").
_AMOUNT_RE = re.compile(
    r"(?:[-–]\s*|(?P<doc_num>\b\d{5,6})\s+)(\d{1,3}(?:\.\d{3})*,\d{2})(-?)"
    r"(?:\s+\d{1,3}(?:\.\d{3})*,\d{2}-?)?\s*$"
)

# Months PT → int
_MONTHS = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

# Lines to skip unconditionally
_SKIP_RE = re.compile(
    r"^(Pagina:|Extrato_PF|BALP_|EXTRATO CONSOLIDADO|"
    r"Fale Conosco|Loja:|Central de Atendimento|De segunda|"
    r"4004 |0800 |Ouvidoria|^SAC$|Reclamações|Todos os dias|"
    r"Libras|Acesse:|Se n[aã]|"
    r"Data\s+Descri|SALDO\s+EM|Dia\s+Saldo|"
    r"D[eé]bito Autom|Compras com Cart[aã]o|Comprovantes|"
    r"Transfer[eê]ncias|Resumo\s*-|"
    r"Nome\s*$|Ag[eê]ncia\s*$|Conta Corrente\s*$|Movimenta[cç][aã]o\s*$|"
    r"\(=\)|\(\+\)|\(-\)|Dep[oó]sitos|Saques|Pagamentos|Outros Cr|"
    r"Saldo de|Prezado|Sua segur|Proteja|Desconfie|N[aã]o caia|"
    r"Se quer|participar|Resumo -|\w+/\d{4}\s*$)",
    re.IGNORECASE,
)

# Stop processing when reaching supplementary sections
_STOP_RE = re.compile(
    r"^(Dia\s+Saldo de|D[eé]bito Autom[aá]tico em|"
    r"Compras com Cart[aã]o de D[eé]bito|"
    r"Comprovantes de Pagamento|Transfer[eê]ncias entre)",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _extract_year(full_text: str) -> int:
    m = re.search(r"(\w+)/(\d{4})", full_text)
    if m and m.group(1).lower() in _MONTHS:
        return int(m.group(2))
    raise ValueError("Could not find year in bank statement header")


def _parse_date(day_month: str, year: int) -> date:
    day, month = map(int, day_month.split("/"))
    return date(year, month, day)


def _build_tx(
    d: date, parts: list[str], instrument_id: str
) -> BankTransactionRow | None:
    """Build a BankTransactionRow from accumulated description parts."""
    if not parts:
        return None
    full = " ".join(p.strip() for p in parts if p.strip())
    m = _AMOUNT_RE.search(full)
    if not m:
        return None

    doc_num = m.group("doc_num")  # 5-6 digit document number, or None
    raw_amount = m.group(2).replace(".", "").replace(",", ".")
    is_debit = m.group(3) == "-"
    amount_minor = to_minor(raw_amount)
    signed = -amount_minor if is_debit else amount_minor

    # Strip amount (and optional balance) from description
    desc_raw = _AMOUNT_RE.sub("", full).strip().strip("-–").strip()
    if not desc_raw:
        return None

    desc_norm = normalize_description(desc_raw)
    # When a document number is present, include it in the fingerprint so that
    # identical-description transactions on the same day (e.g. repeated tolls)
    # are treated as distinct entries.
    fp_desc = f"{desc_norm} {doc_num}" if doc_num else desc_norm
    fp = compute_fingerprint(instrument_id, d, "BRL", signed, fp_desc)
    posted_at = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)

    return BankTransactionRow(
        posted_at=posted_at,
        posted_date=d,
        description_raw=desc_raw,
        description_norm=desc_norm,
        amount_minor=signed,
        currency="BRL",
        source_tx_id=doc_num,
        fingerprint_hash=fp,
        raw_payload={"raw": full},
    )


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

def _parse_transactions(lines: list[str], year: int, instrument_id: str) -> list[BankTransactionRow]:
    rows: list[BankTransactionRow] = []
    in_section = False
    current_date: date | None = None
    acc: list[str] = []  # accumulator for current transaction

    def flush() -> None:
        if acc and current_date:
            tx = _build_tx(current_date, acc, instrument_id)
            if tx:
                rows.append(tx)
        acc.clear()

    for raw in lines:
        line = raw.strip()

        if not in_section:
            if "Movimento (R$)" in line:
                in_section = True
            continue

        if _STOP_RE.match(line):
            break

        if not line or _SKIP_RE.match(line):
            continue

        # New date line
        dm = _DATE_RE.match(line)
        if dm:
            flush()
            current_date = _parse_date(dm.group(1), year)
            rest = dm.group(2).strip()
            if rest:
                acc.append(rest)
                if _AMOUNT_RE.search(rest):
                    flush()
            continue

        if current_date is None:
            continue

        # Continuation / same-date next-tx line
        acc.append(line)
        if _AMOUNT_RE.search(line):
            flush()

    flush()
    return rows


# --------------------------------------------------------------------------- #
# Importer
# --------------------------------------------------------------------------- #

class SantanderBrBankImporter:
    SOURCE_NAME = "santander_br_bank"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        return is_santander_bank(file_bytes)

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        lines: list[str] = []
        full_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            full_parts.append(text)
            lines.extend(text.splitlines())

        year = _extract_year("\n".join(full_parts))
        txs = _parse_transactions(lines, year, instrument_id)
        return ImportResult(bank_transactions=txs)
