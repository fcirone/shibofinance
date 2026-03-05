"""XP BR — credit card statement PDF parser.

The PDF is encrypted with the first 5 digits of the holder's CPF.
Store it as instrument metadata: {"pdf_password": "29232"}.

Structure:
  - Page 0: boleto / payment options
  - Page 1: blank / contact info
  - Page 2: statement summary + first transactions (FABIO CIRONE - XXXX...NNNN)
  - Pages 3+: continuation of transactions, possibly multiple cardholders

Transaction line format:
  DD/MM/YY  DESCRIPTION  AMOUNT_BRL  AMOUNT_USD
  DD/MM/YY  DESCRIPTION - Parcela N/M  AMOUNT_BRL  0,00   (installment)
  DD/MM/YY  IOF Transacoes Exterior R$ AMOUNT_BRL          (IOF tax)

Lines to skip:
  "Subtotal X.XXX,XX"
  "Data Descrição R$ US$"
  "FABIO CIRONE - 4998..." (cardholder section header)
  "Pagamentos Validos Normais -AMOUNT"  (payment credit — handled separately)
  Page headers / footers

Statement info extracted from full text:
  - Due date:      "Vencimento DD/MM/YYYY"
  - Closing date:  "Fatura fechada em DD/MM/YYYY"
  - Total:         "Despesas até a emissão desta fatura X.XXX,XX"
  - Statement start is approximated as closing_date - 35 days (not in PDF)
"""
import io
import re
from datetime import date, datetime, timedelta, timezone

import pypdf

from core.fingerprint import compute_fingerprint
from core.money import to_minor
from core.normalizers import normalize_description
from importers.base import CardStatementRow, CardTransactionRow, ImportResult
from importers.xp_br.detector import is_xp_card

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Statement info
_DUE_DATE_RE = re.compile(r"Vencimento\s+(\d{2}/\d{2}/\d{4})")
_CLOSING_RE = re.compile(r"Fatura fechada em\s+(\d{2}/\d{2}/\d{4})")
_TOTAL_RE = re.compile(r"Despesas até a emissão desta fatura\s+([\d.]+,\d{2})")

# Regular transaction: DD/MM/YY  DESCRIPTION  BRL  USD
_TX_RE = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+(.*?)\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s*$")

# IOF line (no USD column): DD/MM/YY IOF ... R$ AMOUNT
_IOF_RE = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+(IOF\s+.*?)\s+R\$\s*([\d.]+,\d{2})\s*$")

# Payment/credit line — negative amount, skip
_PAYMENT_RE = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+.*-[\d.]+,\d{2}\s*$")

# Installment marker at end of description
_PARCELA_RE = re.compile(r"^(.*?)\s+-\s+Parcela\s+(\d+)/(\d+)\s*$")

# Subtotal line
_SUBTOTAL_RE = re.compile(r"^Subtotal\s+[\d.]+,\d{2}\s*$")

# Cardholder section header: "FABIO CIRONE - 4998********2605"
_CARDHOLDER_RE = re.compile(r"^\S.*-\s*\d{4}\*+\d{4}\s*$")

# Lines to skip
_SKIP_RE = re.compile(
    r"^(Titular|Endereço|Vencimento|Data\s+Descri|As\s+informa|"
    r"\+\s*55|0800|Horário|Entre no|Acesse|Encontre|Vá para|"
    r"Separamos|Pagamento total|Pagamento m[ií]nimo|Parcelamento|"
    r"Olá|Chegou|com\s+vencim|no\s+valor|AVENIDA|CEP:|CNPJ|"
    r"Av\.\s+Chedit|São Paulo|Atendimento|Ouvidoria|www\.|"
    r"Beneﬁci|Local de|Instruções|Pagável|REALIZAR|Aceite|"
    r"Espécie|Nosso|Uso do|Carteira|Quantidade|Banco XP|"
    r"Pagador:|Autenticação|Ficha|Você encontra|nas próximas|"
    r"Resumo da sua|Total da fatura|Pagamentos/créditos|"
    r"Saldo financiado|Saldo credor|Despesas até|Valor total|"
    r"Fatura fechada|Próximo fechamento|Melhor dia|"
    r"2x|13x|24x|R\$\s+\d|Se eu|Caso você|Juros|IOF\s+0|"
    r"CET|Tarifa|Conversão|Emissão|Segunda via|Anuidade|"
    r"Saque|Demais cobranças|Multa|[\d]{5,}|AVENIDA)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    """Parse DD/MM/YY or DD/MM/YYYY."""
    parts = s.split("/")
    d, m = int(parts[0]), int(parts[1])
    y = int(parts[2])
    if y < 100:
        y += 2000
    return date(y, m, d)


def _extract_statement_info(full_text: str) -> tuple[date, date, date | None, int]:
    """Return (statement_start, statement_end/closing, due_date, total_minor)."""
    due_date: date | None = None
    closing_date: date | None = None
    total_minor = 0

    m = _DUE_DATE_RE.search(full_text)
    if m:
        due_date = _parse_date(m.group(1))

    m = _CLOSING_RE.search(full_text)
    if m:
        closing_date = _parse_date(m.group(1))

    m = _TOTAL_RE.search(full_text)
    if m:
        raw = m.group(1).replace(".", "").replace(",", ".")
        total_minor = to_minor(raw)

    if closing_date is None and due_date is not None:
        closing_date = due_date - timedelta(days=8)  # heuristic

    if closing_date is None:
        closing_date = date.today()

    statement_end = closing_date
    statement_start = closing_date - timedelta(days=35)  # approximation

    return statement_start, statement_end, due_date, total_minor


def _build_tx(
    date_str: str,
    desc_raw: str,
    amount_brl: str,
    amount_usd: str,
    credit_card_id: str,
    seen_fps: "Counter | None" = None,
) -> CardTransactionRow | None:
    """Build a CardTransactionRow from parsed fields."""
    posted_date = _parse_date(date_str)
    amount_minor = to_minor(amount_brl.replace(".", "").replace(",", "."))
    if amount_minor <= 0:
        return None  # skip credits/payments

    # Parse installment info from description
    installment_number: int | None = None
    installments_total: int | None = None
    pm = _PARCELA_RE.match(desc_raw)
    if pm:
        desc_raw = pm.group(1).strip()
        installment_number = int(pm.group(2))
        installments_total = int(pm.group(3))

    desc_norm = normalize_description(desc_raw)
    fp = compute_fingerprint(credit_card_id, posted_date, "BRL", amount_minor, desc_norm)
    if seen_fps is not None:
        seen_fps[fp] += 1
        if seen_fps[fp] > 1:
            fp = compute_fingerprint(
                credit_card_id, posted_date, "BRL", amount_minor,
                f"{desc_norm} #{seen_fps[fp]}"
            )
    posted_at = datetime(
        posted_date.year, posted_date.month, posted_date.day, 12, 0, 0, tzinfo=timezone.utc
    )

    usd_val = amount_usd.replace(".", "").replace(",", ".") if amount_usd else "0"
    return CardTransactionRow(
        posted_at=posted_at,
        posted_date=posted_date,
        description_raw=desc_raw,
        description_norm=desc_norm,
        merchant_raw=None,
        amount_minor=amount_minor,
        currency="BRL",
        installments_total=installments_total,
        installment_number=installment_number,
        source_tx_id=None,
        fingerprint_hash=fp,
        raw_payload={"raw": desc_raw, "usd": usd_val},
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_transactions(lines: list[str], credit_card_id: str) -> list[CardTransactionRow]:
    from collections import Counter
    rows: list[CardTransactionRow] = []
    seen_fps: Counter = Counter()
    in_tx_section = False

    for raw in lines:
        line = re.sub(r" {2,}", " ", raw).strip()

        if not line:
            continue

        # Detect start of transaction table
        if re.match(r"^D\s*ata\s+D\s*escri", line, re.IGNORECASE):
            in_tx_section = True
            continue

        if not in_tx_section:
            continue

        # Skip subtotals
        if _SUBTOTAL_RE.match(line):
            continue

        # Skip cardholder section headers
        if _CARDHOLDER_RE.match(line):
            continue

        # Skip payment/credit lines (negative amounts)
        if _PAYMENT_RE.match(line):
            continue

        # Skip general header/footer noise
        if _SKIP_RE.match(line):
            continue

        # IOF tax line
        m = _IOF_RE.match(line)
        if m:
            tx = _build_tx(m.group(1), m.group(2).strip(), m.group(3), "0", credit_card_id, seen_fps)
            if tx:
                rows.append(tx)
            continue

        # Regular transaction
        m = _TX_RE.match(line)
        if m:
            tx = _build_tx(m.group(1), m.group(2).strip(), m.group(3), m.group(4), credit_card_id, seen_fps)
            if tx:
                rows.append(tx)

    return rows


# ---------------------------------------------------------------------------
# Importer
# ---------------------------------------------------------------------------

class XpBrCardImporter:
    SOURCE_NAME = "xp_br_card"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        # The registry filters by instrument.source before calling detect, so
        # by the time we get here we only need to confirm: encrypted PDF.
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            return reader.is_encrypted
        except Exception:
            return False

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,  # this is credit_card instrument_id, not credit_card.id
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        password = (instrument_metadata or {}).get("pdf_password", "")

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            if reader.decrypt(password) == 0:
                raise ValueError(
                    "Could not decrypt XP card PDF — check pdf_password in instrument metadata "
                    "(should be the first 5 digits of your CPF)"
                )

        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        lines = full_text.splitlines()

        statement_start, statement_end, due_date, total_minor = _extract_statement_info(full_text)

        txs = _parse_transactions(lines, instrument_id)

        statement = CardStatementRow(
            statement_start=statement_start,
            statement_end=statement_end,
            closing_date=statement_end,
            due_date=due_date,
            total_minor=total_minor,
            currency="BRL",
            raw_payload={
                "due_date": str(due_date),
                "closing_date": str(statement_end),
                "total_minor": total_minor,
            },
        )

        return ImportResult(card_transactions=txs, card_statements=[statement])
