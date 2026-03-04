import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InstrumentType(str, enum.Enum):
    bank_account = "bank_account"
    credit_card = "credit_card"


class InstrumentSource(str, enum.Enum):
    santander_br = "santander_br"
    xp_br = "xp_br"
    bbva_uy = "bbva_uy"


class Currency(str, enum.Enum):
    BRL = "BRL"
    USD = "USD"
    UYU = "UYU"


class ImportStatus(str, enum.Enum):
    created = "created"
    processed = "processed"
    failed = "failed"


class StatementStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    paid = "paid"
    partial = "partial"


class CategoryKind(str, enum.Enum):
    expense = "expense"
    income = "income"
    transfer = "transfer"


class TargetType(str, enum.Enum):
    bank_transaction = "bank_transaction"
    card_transaction = "card_transaction"


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("source", "source_instrument_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[InstrumentType] = mapped_column(Enum(InstrumentType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[InstrumentSource] = mapped_column(Enum(InstrumentSource), nullable=False)
    source_instrument_id: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    credit_card: Mapped["CreditCard | None"] = relationship(back_populates="instrument", uselist=False)
    bank_transactions: Mapped[list["BankTransaction"]] = relationship(back_populates="instrument")
    import_batches: Mapped[list["ImportBatch"]] = relationship(back_populates="instrument")


# ---------------------------------------------------------------------------
# Credit Cards
# ---------------------------------------------------------------------------


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), unique=True, nullable=False
    )
    billing_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    statement_currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instrument: Mapped["Instrument"] = relationship(back_populates="credit_card")
    statements: Mapped[list["CreditCardStatement"]] = relationship(back_populates="credit_card")
    card_transactions: Mapped[list["CreditCardTransaction"]] = relationship(back_populates="credit_card")


# ---------------------------------------------------------------------------
# Import Batches
# ---------------------------------------------------------------------------


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus), nullable=False, default=ImportStatus.created)
    inserted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    instrument: Mapped["Instrument"] = relationship(back_populates="import_batches")


# ---------------------------------------------------------------------------
# Bank Transactions
# ---------------------------------------------------------------------------


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posted_date: Mapped[date] = mapped_column(Date, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_norm: Mapped[str] = mapped_column(Text, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    source_tx_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instrument: Mapped["Instrument"] = relationship(back_populates="bank_transactions")
    statement_payment_links: Mapped[list["StatementPaymentLink"]] = relationship(
        back_populates="bank_transaction"
    )
    categorization: Mapped["Categorization | None"] = relationship(
        back_populates="bank_transaction",
        primaryjoin="and_(Categorization.target_type=='bank_transaction', "
                    "foreign(Categorization.target_id)==BankTransaction.id)",
        uselist=False,
    )


# ---------------------------------------------------------------------------
# Credit Card Statements
# ---------------------------------------------------------------------------


class CreditCardStatement(Base):
    __tablename__ = "credit_card_statements"
    __table_args__ = (UniqueConstraint("credit_card_id", "statement_start", "statement_end"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=False
    )
    statement_start: Mapped[date] = mapped_column(Date, nullable=False)
    statement_end: Mapped[date] = mapped_column(Date, nullable=False)
    closing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    status: Mapped[StatementStatus] = mapped_column(
        Enum(StatementStatus), nullable=False, default=StatementStatus.open
    )
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    credit_card: Mapped["CreditCard"] = relationship(back_populates="statements")
    card_transactions: Mapped[list["CreditCardTransaction"]] = relationship(back_populates="statement")
    payment_links: Mapped[list["StatementPaymentLink"]] = relationship(back_populates="card_statement")


# ---------------------------------------------------------------------------
# Credit Card Transactions
# ---------------------------------------------------------------------------


class CreditCardTransaction(Base):
    __tablename__ = "credit_card_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=False
    )
    statement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_card_statements.id"), nullable=True
    )
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    posted_date: Mapped[date] = mapped_column(Date, nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_norm: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    installments_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    installment_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_tx_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    credit_card: Mapped["CreditCard"] = relationship(back_populates="card_transactions")
    statement: Mapped["CreditCardStatement | None"] = relationship(back_populates="card_transactions")
    categorization: Mapped["Categorization | None"] = relationship(
        back_populates="card_transaction",
        primaryjoin="and_(Categorization.target_type=='card_transaction', "
                    "foreign(Categorization.target_id)==CreditCardTransaction.id)",
        uselist=False,
    )


# ---------------------------------------------------------------------------
# Statement Payment Links
# ---------------------------------------------------------------------------


class StatementPaymentLink(Base):
    __tablename__ = "statement_payment_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=False
    )
    card_statement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("credit_card_statements.id"), nullable=False
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bank_transaction: Mapped["BankTransaction"] = relationship(back_populates="statement_payment_links")
    card_statement: Mapped["CreditCardStatement"] = relationship(back_populates="payment_links")


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    kind: Mapped[CategoryKind] = mapped_column(Enum(CategoryKind), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parent: Mapped["Category | None"] = relationship("Category", remote_side="Category.id")
    categorizations: Mapped[list["Categorization"]] = relationship(back_populates="category")


# ---------------------------------------------------------------------------
# Categorizations
# ---------------------------------------------------------------------------


class Categorization(Base):
    __tablename__ = "categorizations"
    __table_args__ = (UniqueConstraint("target_type", "target_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="categorizations")
    bank_transaction: Mapped["BankTransaction | None"] = relationship(
        back_populates="categorization",
        primaryjoin="and_(Categorization.target_type=='bank_transaction', "
                    "Categorization.target_id==foreign(BankTransaction.id))",
        uselist=False,
    )
    card_transaction: Mapped["CreditCardTransaction | None"] = relationship(
        back_populates="categorization",
        primaryjoin="and_(Categorization.target_type=='card_transaction', "
                    "Categorization.target_id==foreign(CreditCardTransaction.id))",
        uselist=False,
    )
