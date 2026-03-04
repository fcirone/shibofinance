"""Santander BR importers — auto-registers on import."""
from importers import registry
from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter
from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

# Bank must be registered before card so the unencrypted-PDF check fires first.
registry.register(SantanderBrBankImporter())
registry.register(SantanderBrCardImporter())
