"""BBVA Uruguay importers — auto-registers on import."""
from importers import registry
from importers.bbva_uy.bank_parser_pdf import BbvaUyBankImporter
from importers.bbva_uy.card_parser_pdf import BbvaUyCardImporter

registry.register(BbvaUyBankImporter())
registry.register(BbvaUyCardImporter())
