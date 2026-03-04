"""Description normalisation for fingerprinting and display."""
import re
import unicodedata


def normalize_description(text: str) -> str:
    """Normalise a transaction description.

    Steps:
    1. Lowercase
    2. Remove accents (NFD decompose, strip combining marks)
    3. Collapse consecutive whitespace to a single space
    4. Remove duplicate punctuation (e.g. ',,,' -> ',')
    5. Strip leading/trailing whitespace
    """
    # Lowercase
    text = text.lower()
    # Remove accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove duplicate punctuation
    text = re.sub(r"([^\w\s])\1+", r"\1", text)
    return text.strip()
