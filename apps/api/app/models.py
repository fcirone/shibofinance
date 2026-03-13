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


class CategorizationSource(str, enum.Enum):
    manual = "manual"
    rule = "rule"
    system = "system"


class MatchField(str, enum.Enum):
    description_raw = "description_raw"
    description_norm = "description_norm"
    merchant_raw = "merchant_raw"
    amount_minor = "amount_minor"


class MatchOperator(str, enum.Enum):
    contains = "contains"
    equals = "equals"
    regex = "regex"
    gte = "gte"
    lte = "lte"


class RuleTargetType(str, enum.Enum):
    bank_transaction = "bank_transaction"
    card_transaction = "card_transaction"
    both = "both"


class EventAction(str, enum.Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"


class BudgetPeriodStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class RecurringCadence(str, enum.Enum):
    monthly = "monthly"
    weekly = "weekly"
    yearly = "yearly"
    custom = "custom"


class DetectionSource(str, enum.Enum):
    system = "system"
    manual = "manual"


class RecurringPatternStatus(str, enum.Enum):
    suggested = "suggested"
    approved = "approved"
    ignored = "ignored"


class PayableSourceType(str, enum.Enum):
    manual = "manual"
    recurring_pattern = "recurring_pattern"


class OccurrenceStatus(str, enum.Enum):
    expected = "expected"
    pending = "pending"
    paid = "paid"
    ignored = "ignored"


class AssetClass(str, enum.Enum):
    stock = "stock"
    bond = "bond"
    etf = "etf"
    real_estate = "real_estate"
    crypto = "crypto"
    cash = "cash"
    other = "other"


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
        overlaps="card_transaction",
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
        overlaps="bank_transaction",
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
    rules: Mapped[list["CategoryRule"]] = relationship(back_populates="category")


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
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category_rules.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[CategorizationSource] = mapped_column(
        Enum(CategorizationSource),
        nullable=False,
        default=CategorizationSource.manual,
        server_default="manual",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="categorizations")
    rule: Mapped["CategoryRule | None"] = relationship(back_populates="categorizations", foreign_keys=[rule_id])
    bank_transaction: Mapped["BankTransaction | None"] = relationship(
        back_populates="categorization",
        primaryjoin="and_(Categorization.target_type=='bank_transaction', "
                    "foreign(Categorization.target_id)==BankTransaction.id)",
        uselist=False,
        overlaps="card_transaction",
    )
    card_transaction: Mapped["CreditCardTransaction | None"] = relationship(
        back_populates="categorization",
        primaryjoin="and_(Categorization.target_type=='card_transaction', "
                    "foreign(Categorization.target_id)==CreditCardTransaction.id)",
        uselist=False,
        overlaps="bank_transaction",
    )


# ---------------------------------------------------------------------------
# Category Rules
# ---------------------------------------------------------------------------


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    match_field: Mapped[MatchField] = mapped_column(Enum(MatchField), nullable=False)
    match_operator: Mapped[MatchOperator] = mapped_column(Enum(MatchOperator), nullable=False)
    match_value: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[RuleTargetType] = mapped_column(Enum(RuleTargetType), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["Category"] = relationship(back_populates="rules")
    categorizations: Mapped[list["Categorization"]] = relationship(
        back_populates="rule", foreign_keys="Categorization.rule_id"
    )


# ---------------------------------------------------------------------------
# Categorization Events
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Budget Planning
# ---------------------------------------------------------------------------


class BudgetPeriod(Base):
    __tablename__ = "budget_periods"
    __table_args__ = (UniqueConstraint("year", "month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BudgetPeriodStatus] = mapped_column(
        Enum(BudgetPeriodStatus), nullable=False, default=BudgetPeriodStatus.open, server_default="open"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category_budgets: Mapped[list["CategoryBudget"]] = relationship(
        back_populates="budget_period", cascade="all, delete-orphan"
    )


class CategoryBudget(Base):
    __tablename__ = "category_budgets"
    __table_args__ = (UniqueConstraint("budget_period_id", "category_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budget_periods.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    planned_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    budget_period: Mapped["BudgetPeriod"] = relationship(back_populates="category_budgets")
    category: Mapped["Category"] = relationship()


# ---------------------------------------------------------------------------
# Payables and Recurring Expenses
# ---------------------------------------------------------------------------


class RecurringPattern(Base):
    __tablename__ = "recurring_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_description: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    expected_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cadence: Mapped[RecurringCadence] = mapped_column(
        Enum(RecurringCadence), nullable=False, default=RecurringCadence.monthly
    )
    detection_source: Mapped[DetectionSource] = mapped_column(
        Enum(DetectionSource), nullable=False, default=DetectionSource.system
    )
    status: Mapped[RecurringPatternStatus] = mapped_column(
        Enum(RecurringPatternStatus), nullable=False, default=RecurringPatternStatus.suggested
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category | None"] = relationship()
    payables: Mapped[list["Payable"]] = relationship(back_populates="recurring_pattern")


class Payable(Base):
    __tablename__ = "payables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    default_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[PayableSourceType] = mapped_column(
        Enum(PayableSourceType), nullable=False, default=PayableSourceType.manual
    )
    recurring_pattern_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurring_patterns.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category | None"] = relationship()
    recurring_pattern: Mapped["RecurringPattern | None"] = relationship(back_populates="payables")
    occurrences: Mapped[list["PayableOccurrence"]] = relationship(
        back_populates="payable", cascade="all, delete-orphan"
    )


class PayableOccurrence(Base):
    __tablename__ = "payable_occurrences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payables.id", ondelete="CASCADE"), nullable=False
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    actual_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[OccurrenceStatus] = mapped_column(
        Enum(OccurrenceStatus), nullable=False, default=OccurrenceStatus.expected
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    payable: Mapped["Payable"] = relationship(back_populates="occurrences")


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------


class InvestmentAccount(Base):
    __tablename__ = "investment_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    positions: Mapped[list["AssetPosition"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[AssetClass] = mapped_column(Enum(AssetClass), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    positions: Mapped[list["AssetPosition"]] = relationship(back_populates="asset")


class AssetPosition(Base):
    __tablename__ = "asset_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_accounts.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_cost_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_value_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    account: Mapped["InvestmentAccount"] = relationship(back_populates="positions")
    asset: Mapped["Asset"] = relationship(back_populates="positions")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (UniqueConstraint("snapshot_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["PortfolioSnapshotItem"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class PortfolioSnapshotItem(Base):
    __tablename__ = "portfolio_snapshot_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False
    )
    investment_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_accounts.id"), nullable=False
    )
    asset_name: Mapped[str] = mapped_column(Text, nullable=False)
    asset_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_class: Mapped[AssetClass] = mapped_column(Enum(AssetClass), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_value_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    snapshot: Mapped["PortfolioSnapshot"] = relationship(back_populates="items")


# ---------------------------------------------------------------------------
# Categorization Events
# ---------------------------------------------------------------------------


class CategorizationEvent(Base):
    __tablename__ = "categorization_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categorization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_type: Mapped[RuleTargetType] = mapped_column(Enum(RuleTargetType), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[EventAction] = mapped_column(Enum(EventAction), nullable=False)
    source: Mapped[CategorizationSource] = mapped_column(Enum(CategorizationSource), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
