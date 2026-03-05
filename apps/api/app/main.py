import importers.santander_br  # noqa: F401 — registers importers on startup
import importers.xp_br  # noqa: F401 — registers importers on startup
import importers.bbva_uy  # noqa: F401 — registers importers on startup

from fastapi import FastAPI

from app.routers import (
    bank_transactions,
    card_transactions,
    categories,
    health,
    imports,
    instruments,
    spending_summary,
    statements,
)

app = FastAPI(title="Finance OS", version="0.1.0")

app.include_router(health.router)
app.include_router(instruments.router)
app.include_router(imports.router)
app.include_router(bank_transactions.router)
app.include_router(card_transactions.router)
app.include_router(statements.router)
app.include_router(categories.router)
app.include_router(spending_summary.router)
