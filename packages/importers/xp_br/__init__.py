"""XP BR importers — auto-registers on import."""
from importers import registry
from importers.xp_br.bank_parser_pdf import XpBrBankImporter
from importers.xp_br.card_parser_pdf import XpBrCardImporter

registry.register(XpBrBankImporter())
registry.register(XpBrCardImporter())
