"""Quick import script — creates instruments and imports Santander BR sample PDFs.

Usage (inside the api container):
    python tools/import_santander.py

Or from the host:
    docker compose exec api python tools/import_santander.py

Environment variables (optional):
    SANTANDER_CPF   — CPF used to encrypt the card PDF (default: 29232916894)
    BANK_PDF        — path to bank statement PDF
    CARD_PDF        — path to card statement PDF
"""
import asyncio
import os
import sys
from pathlib import Path

# Make sure packages are on sys.path when run from repo root.
sys.path.insert(0, "/app")
sys.path.insert(0, "/packages")

import importers.santander_br  # noqa: F401 — registers importers

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import CreditCard, Instrument, InstrumentSource, InstrumentType
from app.services.import_service import run_import

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://finance:finance@db:5432/finance"
)
BANK_PDF = Path(os.environ.get("BANK_PDF", "/data/samples/santander_br/santander_extrato_conta.pdf"))
CARD_PDF = Path(os.environ.get("CARD_PDF", "/data/samples/santander_br/santander_cartao.pdf"))
CPF = os.environ.get("SANTANDER_CPF", "29232916894")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_or_create_instrument(session: AsyncSession, name: str, itype: InstrumentType, metadata_: dict) -> Instrument:
    inst = await session.scalar(
        select(Instrument).where(Instrument.name == name)
    )
    if inst:
        print(f"  [existing] instrument '{name}' ({inst.id})")
        return inst
    inst = Instrument(
        name=name,
        type=itype,
        source=InstrumentSource.santander_br,
        currency="BRL",
        metadata_=metadata_,
    )
    session.add(inst)
    await session.flush()
    print(f"  [created]  instrument '{name}' ({inst.id})")
    return inst


async def get_or_create_credit_card(session: AsyncSession, instrument: Instrument) -> CreditCard:
    cc = await session.scalar(
        select(CreditCard).where(CreditCard.instrument_id == instrument.id)
    )
    if cc:
        return cc
    cc = CreditCard(instrument_id=instrument.id, last4=None, brand=None)
    session.add(cc)
    await session.flush()
    return cc


async def main() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            print("\n=== Santander BR — Import Script ===\n")

            # --- Bank account ---
            if BANK_PDF.exists():
                print(f"Importing bank statement: {BANK_PDF.name}")
                bank_inst = await get_or_create_instrument(
                    session,
                    name="Santander BR — Conta Corrente",
                    itype=InstrumentType.bank_account,
                    metadata_={},
                )
                batch = await run_import(session, bank_inst, BANK_PDF.read_bytes(), BANK_PDF.name)
                print(f"  inserted={batch.inserted_count}  duplicates={batch.duplicate_count}  status={batch.status}\n")
            else:
                print(f"Bank PDF not found, skipping: {BANK_PDF}\n")

            # --- Credit card ---
            if CARD_PDF.exists():
                print(f"Importing card statement:  {CARD_PDF.name}")
                card_inst = await get_or_create_instrument(
                    session,
                    name="Santander BR — Cartão de Crédito",
                    itype=InstrumentType.credit_card,
                    metadata_={"pdf_password": CPF},
                )
                await get_or_create_credit_card(session, card_inst)
                batch = await run_import(session, card_inst, CARD_PDF.read_bytes(), CARD_PDF.name)
                print(f"  inserted={batch.inserted_count}  duplicates={batch.duplicate_count}  status={batch.status}\n")
            else:
                print(f"Card PDF not found, skipping: {CARD_PDF}\n")

        # Summary queries
        print("=== Summary ===")
        rows = await session.execute(text(
            "SELECT 'bank_transactions' AS tbl, COUNT(*) FROM bank_transactions"
            " UNION ALL "
            "SELECT 'credit_card_transactions', COUNT(*) FROM credit_card_transactions"
            " UNION ALL "
            "SELECT 'credit_card_statements', COUNT(*) FROM credit_card_statements"
        ))
        for tbl, count in rows:
            print(f"  {tbl}: {count} rows")
        print()


if __name__ == "__main__":
    asyncio.run(main())
