"""Importer registry — auto-detects which importer to use for a given file."""
from importers.base import BaseImporter

_registry: list[BaseImporter] = []


def register(importer: BaseImporter) -> None:
    _registry.append(importer)


def detect(file_bytes: bytes, filename: str, source_hint: str | None = None) -> BaseImporter:
    """Return the first registered importer that claims the file.

    If *source_hint* is provided (e.g. "santander_br"), only importers whose
    SOURCE_NAME starts with that value are considered.  This avoids ambiguity
    between banks that share the same file format (e.g. both Santander and XP
    use encrypted PDFs for credit cards).

    Raises ValueError if no importer matches.
    """
    candidates = _registry
    if source_hint:
        candidates = [i for i in _registry if i.SOURCE_NAME.startswith(source_hint)]
    for imp in candidates:
        if imp.detect(file_bytes, filename):
            return imp
    raise ValueError(f"No importer found for file: {filename!r}")


def registered_sources() -> list[str]:
    return [imp.SOURCE_NAME for imp in _registry]
