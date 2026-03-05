"""Detection helpers for XP BR files."""
import io

import pypdf

# Bank: unencrypted PDF — "Banco XP" appears in the header without font spacing
BANK_MARKER = "Banco XP"

# Card: encrypted PDF, contains these after decryption
CARD_MARKER = "Cartão XP"


def _read_all_text(file_bytes: bytes, password: str = "") -> str | None:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            if reader.decrypt(password) == 0:
                return None
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None


def is_xp_bank(file_bytes: bytes) -> bool:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            return False
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return BANK_MARKER in text
    except Exception:
        return False


def is_xp_card(file_bytes: bytes, password: str = "") -> bool:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if not reader.is_encrypted:
            return False
        if reader.decrypt(password) == 0:
            return False
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return CARD_MARKER in text
    except Exception:
        return False
