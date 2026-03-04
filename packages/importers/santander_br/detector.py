"""Detection helpers for Santander BR files."""
import io

import pypdf

BANK_MARKER = "EXTRATO CONSOLIDADO INTELIGENTE"
CARD_MARKER = "Detalhamento da Fatura"


def _pdf_first_page_text(file_bytes: bytes, password: str = "") -> str | None:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            if reader.decrypt(password) == 0:
                return None
        return reader.pages[0].extract_text() or ""
    except Exception:
        return None


def is_santander_bank(file_bytes: bytes) -> bool:
    text = _pdf_first_page_text(file_bytes)
    return text is not None and BANK_MARKER in text


def is_santander_card(file_bytes: bytes, password: str = "") -> bool:
    """Returns True if file is an encrypted PDF that decrypts with the given
    password and contains the Santander card marker."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if not reader.is_encrypted:
            return False
        if reader.decrypt(password) == 0:
            return False
        # Search all pages for the card marker
        for page in reader.pages:
            if CARD_MARKER in (page.extract_text() or ""):
                return True
        return False
    except Exception:
        return False
