import importers.santander_br  # noqa: F401 — registers importers on startup
import importers.xp_br  # noqa: F401 — registers importers on startup
import importers.bbva_uy  # noqa: F401 — registers importers on startup

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Category, CategoryKind
from app.routers import (
    bank_transactions,
    budgets,
    card_transactions,
    categories,
    categorizations,
    category_rules,
    health,
    imports,
    instruments,
    payables,
    spending_summary,
    statements,
)

_DEFAULT_CATEGORIES: list[tuple[str, CategoryKind]] = [
    ("Food & Dining", CategoryKind.expense),
    ("Transport", CategoryKind.expense),
    ("Shopping", CategoryKind.expense),
    ("Health", CategoryKind.expense),
    ("Entertainment", CategoryKind.expense),
    ("Housing & Rent", CategoryKind.expense),
    ("Utilities", CategoryKind.expense),
    ("Travel", CategoryKind.expense),
    ("Salary", CategoryKind.income),
    ("Other Income", CategoryKind.income),
    ("transfer", CategoryKind.transfer),
]


async def _seed_categories() -> None:
    async with AsyncSessionLocal() as db:
        for name, kind in _DEFAULT_CATEGORIES:
            existing = await db.scalar(select(Category).where(Category.name == name))
            if not existing:
                db.add(Category(name=name, kind=kind))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _seed_categories()
    yield


app = FastAPI(title="Shibo Finance", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)

app.include_router(health.router)
app.include_router(instruments.router)
app.include_router(imports.router)
app.include_router(bank_transactions.router)
app.include_router(card_transactions.router)
app.include_router(statements.router)
app.include_router(categories.router)
app.include_router(categorizations.router)
app.include_router(category_rules.router)
app.include_router(spending_summary.router)
app.include_router(budgets.router)
app.include_router(payables.router)
