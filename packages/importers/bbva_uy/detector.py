"""BBVA Uruguay — file detectors.

Bank statement:  encrypted PDF, empty password, contains "Cuentas Corrientes"
Card statement:  unencrypted PDF, contains "Fecha de cierre"
"""
import io

import pypdf

_BANK_MARKER = "Cuentas Corrientes"
_CARD_MARKER = "Fecha de cierre"


def _extract_text(reader: pypdf.PdfReader) -> str:
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def is_bbva_bank(file_bytes: bytes) -> bool:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            if reader.decrypt("") == 0:
                return False
        text = _extract_text(reader)
        return _BANK_MARKER in text and "bbva" in text.lower()
    except Exception:
        return False


def is_bbva_card(file_bytes: bytes) -> bool:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            return False
        text = _extract_text(reader)
        return _CARD_MARKER in text and "bbva" in text.lower()
    except Exception:
        return False
