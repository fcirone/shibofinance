"""Importer registry — auto-detects which importer to use for a given file."""
from importers.base import BaseImporter

_registry: list[BaseImporter] = []


def register(importer: BaseImporter) -> None:
    _registry.append(importer)


def detect(file_bytes: bytes, filename: str) -> BaseImporter:
    """Return the first registered importer that claims the file.

    Raises ValueError if no importer matches.
    """
    for imp in _registry:
        if imp.detect(file_bytes, filename):
            return imp
    raise ValueError(f"No importer found for file: {filename!r}")


def registered_sources() -> list[str]:
    return [imp.SOURCE_NAME for imp in _registry]
