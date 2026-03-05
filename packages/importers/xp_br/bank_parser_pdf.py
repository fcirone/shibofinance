"""XP BR — bank statement (Conta Digital) PDF parser.

Format (unencrypted PDF):

Header line:
  Data Descrição Valor Saldo   (with extra spaces due to font encoding)

Transaction lines after header:
  DD/MM/YY às HH:MM:SS  DESCRIPTION  [-]R$  VALUE  R$  SALDO

Examples:
  29/01/26 às 15:56:06 Pix enviado para M onize Alves da M ota -R $  180,00 R $  0,00
  29/01/26 às 15:55:37 Transferência recebida da conta investim ento R $  180,00 R $  180,00

Notes:
  - Amount sign: -R$ = debit, R$ = credit
  - Balance column is ignored
  - Extra spaces inside words are a PDF font artifact; we collapse them
"""
import io
import re
from datetime import date, datetime, timezone

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import BankTransactionRow, ImportResult
from importers.xp_br.detector import is_xp_bank

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Transaction line: DD/MM/YY às HH:MM:SS ...
_LINE_RE = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+às\s+(\d{2}:\d{2}:\d{2})\s+(.*)")

# Amount pattern: optional leading '-', then R$, then value
# Handles "R $ 180,00", "R$180,00", "-R $ 180,00"
_AMOUNT_RE = re.compile(r"(-?)R\s*\$\s*([\d.]+,\d{2})")

# Lines to skip unconditionally
_SKIP_RE = re.compile(
    r"^(D\s*ata|Saldo\s+dispon|Extrato\s+simples|Importante|"
    r"Banco\s+XP|Av\.|CEP|CNPJ|Atendimento|Ouvidoria|w\s*w\s*w\s*\.|"
    r"Este\s+material|Em\s+caso|Para\s+reclama|Para\s+acesso|"
    r"as\s+informa|inform|ser|Caso|04551|acess|4003|0800|SAC)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_line(raw: str) -> str:
    """Collapse multiple consecutive spaces to a single space."""
    return re.sub(r" {2,}", " ", raw).strip()


def _parse_date(date_str: str) -> date:
    """Parse DD/MM/YY into a date object."""
    d, m, y = date_str.split("/")
    year = 2000 + int(y)
    return date(year, int(m), int(d))


def _extract_transactions(lines: list[str], instrument_id: str) -> list[BankTransactionRow]:
    rows: list[BankTransactionRow] = []
    in_section = False

    for raw in lines:
        line = _normalize_line(raw)

        if not in_section:
            # Start after the column header line
            if re.match(r"D?\s*ata\s+D?\s*escri", line, re.IGNORECASE):
                in_section = True
            continue

        if not line or _SKIP_RE.match(line):
            continue

        m = _LINE_RE.match(line)
        if not m:
            continue

        date_str, _time, rest = m.group(1), m.group(2), m.group(3)

        # Find all amounts in the rest of the line
        amount_matches = list(_AMOUNT_RE.finditer(rest))
        if len(amount_matches) < 2:
            continue  # need at least value + saldo

        # Second-to-last = transaction value, last = saldo (ignored)
        val_match = amount_matches[-2]
        sign = val_match.group(1)  # "-" or ""
        raw_val = val_match.group(2).replace(".", "").replace(",", ".")
        amount_minor = to_minor(raw_val)
        signed = -amount_minor if sign == "-" else amount_minor

        # Description = everything before the value match
        desc_raw = rest[: val_match.start()].strip()
        # Remove trailing amount artifacts (e.g., leftover "-")
        desc_raw = re.sub(r"\s*-\s*$", "", desc_raw).strip()
        if not desc_raw:
            continue

        posted_date = _parse_date(date_str)
        desc_norm = normalize_description(desc_raw)
        fp = compute_fingerprint(instrument_id, posted_date, "BRL", signed, desc_norm)
        posted_at = datetime(
            posted_date.year, posted_date.month, posted_date.day, 12, 0, 0, tzinfo=timezone.utc
        )

        rows.append(
            BankTransactionRow(
                posted_at=posted_at,
                posted_date=posted_date,
                description_raw=desc_raw,
                description_norm=desc_norm,
                amount_minor=signed,
                currency="BRL",
                source_tx_id=None,
                fingerprint_hash=fp,
                raw_payload={"raw": raw},
            )
        )

    return rows


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------

class XpBrBankImporter:
    SOURCE_NAME = "xp_br_bank"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        return is_xp_bank(file_bytes)

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        lines: list[str] = []
        for page in reader.pages:
            lines.extend((page.extract_text() or "").splitlines())

        txs = _extract_transactions(lines, instrument_id)
        return ImportResult(bank_transactions=txs)
