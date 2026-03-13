# Shibo Finance — Local Personal Finance System

> See also: [docs/UI_SPEC.md](docs/UI_SPEC.md) — Frontend UI specification (Cycle 1)
> See also: [docs/TASKS.md](docs/TASKS.md) — Execution plan with phase-by-phase tasks

## Objective

Build a local-first personal finance system capable of importing financial data from:

Brazil
- Santander bank statement
- Santander credit card
- XP bank statement
- XP credit card

Uruguay
- BBVA bank statement
- BBVA credit card

The system must normalize all financial data into a single ledger and allow categorization of expenses across both bank transactions and credit card transactions.

The system runs entirely locally using Docker.

No cloud dependencies.

The system must provide:

- API (FastAPI)
- CLI importer
- Postgres database
- Plugin-based importers
- Categorization engine
- Idempotent imports
- Support for credit card statements and linking card payments with bank transactions.

---

# Core Design Principles

1. Local-first architecture
2. Never lose original data
3. Idempotent imports
4. Unified categorization across bank and card transactions
5. Plugin-based importers for each bank
6. Raw data always stored for audit
7. Credit card purchases are expenses
8. Credit card bill payments are transfers (not expenses)

---

# Technology Stack

Python 3.12  
FastAPI  
Uvicorn  
Postgres 16  
SQLAlchemy 2.x  
Alembic  
Pydantic v2  
Docker Compose  
Pytest  

---

# Repository Structure

shibofinance/

CLAUDE.md  
README.md  
.env.example  
docker-compose.yml  
Makefile
.gitignore  

apps/
api/

pyproject.toml  
alembic.ini  

app/

main.py  
settings.py  
db.py  
models.py  
schemas.py  

routers/

health.py  
instruments.py  
imports.py  
bank_transactions.py  
card_transactions.py  
statements.py  
categories.py  

services/

import_service.py  
dedupe_service.py  
fingerprint_service.py  
statement_matcher.py  

alembic/

env.py  
versions/

tests/

test_health.py  
test_import_idempotency.py  

packages/

core/

money.py  
fingerprint.py  
normalizers.py  
timezones.py  

importers/

base.py  
registry.py  

santander_br/
detector.py  
bank_parser_csv.py  
card_parser_csv.py  

xp_br/
detector.py  
bank_parser_csv.py  
card_parser_csv.py  

bbva_uy/
detector.py  
bank_parser_csv.py  
card_parser_csv.py  

tools/

import_cli.py  

data/

samples/

santander_br/  
xp_br/  
bbva_uy/  

---

# Financial Model

The system must model two financial instruments:

- Bank accounts
- Credit cards

Transactions originate from these instruments.

---

# Instruments Table

Represents either a bank account or a credit card.

Fields

id (uuid pk)

type  
bank_account | credit_card

name

source  
santander_br  
xp_br  
bbva_uy

source_instrument_id  
stable identifier defined by user

currency  
BRL  
USD  
UYU

metadata jsonb  
example:

{
 "last4": "1234",
 "brand": "visa"
}

created_at

Unique constraint

(source, source_instrument_id)

---

# Credit Cards Table

Specific properties for credit cards.

Fields

id uuid pk

instrument_id uuid fk instruments.id unique

billing_day int nullable

due_day int nullable

statement_currency

created_at

---

# Import Batches

Tracks every import operation.

Fields

id uuid pk

instrument_id

filename

sha256

status  
created | processed | failed

inserted_count

duplicate_count

error_count

created_at

processed_at

---

# Bank Transactions

Represents transactions from bank accounts.

Fields

id uuid pk

instrument_id

posted_at timestamp UTC

posted_date date

description_raw

description_norm

amount_minor signed bigint

currency

source_tx_id nullable

fingerprint_hash

import_batch_id

raw_payload jsonb

created_at

---

# Credit Card Statements

Represents a credit card billing cycle.

Fields

id uuid pk

credit_card_id

statement_start date

statement_end date

closing_date date nullable

due_date date nullable

total_minor bigint

currency

status  
open | closed | paid | partial

import_batch_id

raw_payload jsonb

created_at

Unique

(credit_card_id, statement_start, statement_end)

---

# Credit Card Transactions

Represents purchases and adjustments on a credit card.

Fields

id uuid pk

credit_card_id

statement_id nullable

posted_at

posted_date

description_raw

description_norm

merchant_raw nullable

amount_minor bigint

currency

installments_total nullable

installment_number nullable

source_tx_id nullable

fingerprint_hash

import_batch_id

raw_payload jsonb

created_at

---

# Statement Payment Links

Links bank transactions with credit card statements.

Fields

id uuid pk

bank_transaction_id

card_statement_id

amount_minor

created_at

Used to represent payments toward a credit card bill.

---

# Categories

Fields

id uuid pk

name

parent_id nullable

kind

expense  
income  
transfer

created_at

---

# Categorization Table

Allows categorizing both bank and card transactions.

Fields

id uuid pk

target_type

bank_transaction  
card_transaction

target_id

category_id

confidence nullable

rule_id nullable

created_at

updated_at

Unique

(target_type, target_id)

---

# Money Rules

All monetary values stored as integer minor units.

Example

100.50 BRL stored as 10050.

---

# Timezone Rules

All timestamps stored in UTC.

Importer defines default timezone.

Brazil  
America/Sao_Paulo

Uruguay  
America/Montevideo

---

# Fingerprint Algorithm

Used when source_tx_id is missing.

SHA256 of

instrument_id  
posted_date  
currency  
amount_minor  
description_norm

Description normalization

lowercase  
remove accents  
collapse whitespace  
remove punctuation duplicates  

---

# Importer Plugin System

Each importer must implement:

SOURCE_NAME

detect(file_bytes, filename) -> bool

parse(file_bytes, instrument_id) -> ImportResult

ImportResult contains

bank_transactions list  
card_transactions list  
card_statements list  

---

# Supported Importers

Santander Brazil

bank PDF  
credit card PDF  

XP Brazil

bank CSV  
credit card CSV  

BBVA Uruguay

bank CSV  
credit card PDF  


---

# Import Pipeline

1 Detect importer  
2 Parse rows  
3 Normalize data  
4 Generate fingerprints  
5 Upsert transactions idempotently  
6 Create or update statements  
7 Attempt automatic statement payment matching  

---

# Payment Matching Logic

When importing bank transactions:

If description contains patterns:

PAGAMENTO FATURA  
PAGTO CARTAO  
CARD PAYMENT  

Then attempt match with card statement where:

amount matches total or partial  
date near statement due date

Create record in statement_payment_links.

Mark category as transfer.

---

# API Endpoints

GET /health

POST /instruments

GET /instruments

POST /imports/upload

GET /bank-transactions

GET /card-transactions

GET /card-statements

POST /categorize

GET /categories

GET /spending-summary

---

# Spending Summary Rules

Expenses =

card_transactions  
+ bank_transactions excluding transfers and card payments.

---

# CLI Tool

tools/import_cli.py

Commands

import

python tools/import_cli.py import \
--file path \
--instrument <instrument_id> \
--source auto

list-transactions

python tools/import_cli.py list-transactions \
--instrument <instrument_id>

---

# Docker Compose

Services

db  
postgres:16

api  
fastapi app

pgadmin optional

---

# Makefile Commands

make up  
make down  
make logs  
make migrate  
make test  
make api-shell

---

# Sample Files

I will add samples files later

---

# Tests

pytest suite must include

health endpoint test

import idempotency test

fingerprint consistency test

basic query test

---

# Implementation Order

1 Create repo skeleton  
2 Docker compose  
3 Database models  
4 Alembic migrations  
5 Import framework  
6 Santander importer  
7 API endpoints  
8 CLI tool  
9 Tests  

---

# Acceptance Criteria

docker compose up starts system

API reachable

Create instruments

Upload CSV

Transactions imported

Reimport same file produces duplicates only

Queries return expected results

---

# Backend Status (Stable — Do Not Change)

The backend is complete and stable. All phases 1–13 are done (112 tests passing).

**Do NOT modify backend code or database schema** unless strictly necessary to expose an already-existing capability via a new read-only endpoint. Currently planned minimal additions:
- `GET /imports` — list import batches (existing table, not yet exposed)
- `GET /imports/{id}` — single batch detail
- CORS middleware — required for browser-based frontend to call the API

**Existing API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /instruments | List instruments |
| POST | /instruments | Create instrument |
| PATCH | /instruments/{id} | Update instrument name/metadata |
| POST | /imports/upload | Upload + process statement file |
| GET | /bank-transactions | List bank transactions (filter: instrument_id, date_from, date_to, limit, offset) |
| GET | /card-transactions | List card transactions (filter: instrument_id, date_from, date_to, limit, offset) |
| GET | /card-statements | List card statements (filter: instrument_id) |
| GET | /categories | List categories |
| POST | /categorize | Categorize a transaction |
| GET | /spending-summary | Spending totals (required: date_from, date_to; optional: instrument_id) |

OpenAPI schema available at: `http://localhost:8000/openapi.json`

---

# Frontend

## Scope

### Cycle 1 (MVP UI) — In Scope
- Create and manage instruments (bank accounts + credit cards)
- Upload statement files (PDF/CSV) for an instrument
- View import history and batch results
- View all transactions (bank + card) with filters, date range, pagination
- View credit card statements with detail drawer
- Dashboard overview: spending summary chart + recent imports + quick actions

### Out of Scope for Cycle 1
- Categorization UI (assign categories to transactions)
- Categorization rules engine / auto-categorization
- Budget goals
- Multi-user / authentication
- Cloud deployment
- CSV export
- Mobile app

---

## Frontend Technology Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 15 (App Router) + TypeScript |
| Styling | Tailwind CSS v4 |
| Component library | shadcn/ui |
| Data fetching / caching | TanStack Query (React Query) v5 |
| Form management | React Hook Form v7 |
| Validation | Zod v3 |
| Charts | Recharts v2 |
| API types | openapi-typescript (generated from `/openapi.json`) |
| Icons | Lucide React |
| Notifications | shadcn/ui Sonner (toast) |

---

## Repository Structure (Frontend)

```
apps/
  web/
    src/
      app/                    # Next.js App Router pages
        layout.tsx            # Root layout with AppShell
        page.tsx              # / Dashboard
        instruments/
          page.tsx            # /instruments
        import/
          new/
            page.tsx          # /import/new
        imports/
          page.tsx            # /imports
        transactions/
          page.tsx            # /transactions
        statements/
          page.tsx            # /statements
      components/
        shell/
          AppShell.tsx
          Sidebar.tsx
          Topbar.tsx
        instruments/
          InstrumentCard.tsx
          InstrumentPicker.tsx
          CreateInstrumentDialog.tsx
          EditInstrumentDialog.tsx
        imports/
          UploadDropzone.tsx
          ImportBatchCard.tsx
          BatchDetailDrawer.tsx
        transactions/
          TransactionsTable.tsx
          TransactionFilters.tsx
          AmountDisplay.tsx
        statements/
          StatementCard.tsx
          StatementDetailDrawer.tsx
        dashboard/
          SummaryCards.tsx
          SpendingChart.tsx
          RecentImportsWidget.tsx
        ui/                   # shadcn/ui primitives (generated)
        shared/
          EmptyState.tsx
          LoadingSkeleton.tsx
          StatusBadge.tsx
          SourceBadge.tsx
          DateRangePicker.tsx
          PageHeader.tsx
      lib/
        api.ts                # Typed API client (wraps fetch)
        api-types.ts          # Generated from OpenAPI (do not edit by hand)
        utils.ts              # Currency formatting, date helpers
        query-client.ts       # TanStack Query client singleton
      hooks/
        useInstruments.ts
        useImports.ts
        useBankTransactions.ts
        useCardTransactions.ts
        useStatements.ts
        useSpendingSummary.ts
    public/
    package.json
    tsconfig.json
    tailwind.config.ts
    next.config.ts
    Dockerfile
```

---

## API Client Conventions

### Type Generation
```bash
# Run after any backend schema change
npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts
```

### API Client (`src/lib/api.ts`)
- Base URL read from `process.env.NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`)
- All functions return typed responses
- Non-2xx responses throw `ApiError` with `.message` and `.status`
- No third-party HTTP library — raw `fetch` only

```typescript
// Pattern for every API call
export async function getInstruments(): Promise<InstrumentOut[]> {
  const res = await apiFetch("/instruments");
  return res.json();
}
```

### TanStack Query Conventions
- One custom hook per resource (`useInstruments`, `useBankTransactions`, etc.)
- Query keys follow the pattern `["resource", filters]`
- `staleTime: 30_000` (30s) for reference data (instruments, categories)
- `staleTime: 0` for transactions (always fresh)
- Mutations call `queryClient.invalidateQueries` on success

---

## Routing Conventions

- All pages are Server Components by default (Next.js App Router)
- Data-fetching interactive components use `"use client"` + TanStack Query
- URL search params are the source of truth for filters (instrument_id, date_from, date_to, tab, page)
- Use `useRouter` + `useSearchParams` for filter state — no separate React state for filters

---

## Forms & Validation Conventions

```typescript
// Pattern for every form
const schema = z.object({ name: z.string().min(2) });
type FormData = z.infer<typeof schema>;

const form = useForm<FormData>({ resolver: zodResolver(schema) });
```

- All form schemas defined with Zod, co-located with the component
- `React Hook Form` + `zodResolver` for all forms
- Inline error messages under each field
- Submit button disabled while `form.formState.isSubmitting`

---

## Error Handling Conventions

- **Query errors:** caught by TanStack Query; display toast via `onError` callback
- **Mutation errors:** `onError` callback shows toast with `error.message`
- **Form errors:** inline field messages from RHF
- **Network down:** global error boundary catches query failures with helpful message
- Never swallow errors silently

---

## Amount Display Convention

All monetary values arrive as integer minor units. Always format before display:

```typescript
// src/lib/utils.ts
export function formatAmount(minor: number, currency: string): string {
  const value = minor / 100;
  if (currency === "BRL") return `R$ ${value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
  if (currency === "UYU") return `$ U ${value.toLocaleString("es-UY", { minimumFractionDigits: 2 })}`;
  return `$ ${value.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;  // USD default
}
```

Negative amounts → red text (`text-destructive`).
Positive amounts → default foreground.

---

## Docker Compose (Planned Addition)

Add a `web` service to `docker-compose.yml`:

```yaml
web:
  build:
    context: ./apps/web
    dockerfile: Dockerfile
  ports:
    - "3000:3000"
  environment:
    NEXT_PUBLIC_API_BASE_URL: http://api:8000
  volumes:
    - ./apps/web:/app
    - /app/node_modules
    - /app/.next
  depends_on:
    - api
  command: npm run dev
```

The `api` service must add CORS middleware to allow requests from `http://localhost:3000`.

---

## Makefile Commands (Planned)

```makefile
web-dev:    docker compose run --rm --service-ports web npm run dev
web-build:  docker compose run --rm web npm run build
web-test:   docker compose run --rm web npm test
web-lint:   docker compose run --rm web npm run lint
web-types:  docker compose run --rm web npx openapi-typescript http://api:8000/openapi.json -o src/lib/api-types.ts
```

---

## UX Principles

1. **Premium SaaS feel** — generous whitespace, consistent spacing, polished hover/focus states
2. **Data density without clutter** — tables show what matters; secondary info in drawers
3. **Zero ambiguity** — every empty state tells the user what to do next
4. **Skeleton-first loading** — no layout shift; skeletons match real content shape
5. **Errors are informative** — toast messages include the backend error message when available
6. **Neutral copy** — not personalized; works for any user with any bank

---

# Transaction Categorization System

## Concept

- Categories are shared between bank and credit card transactions.
- A transaction can have at most one active categorization (unique constraint on `target_type, target_id`).
- Manual categorization always takes precedence over system or rule-based categorization.
- Categories are hierarchical: a category may have a `parent_id` pointing to another category.
- Each category has a `kind` (expense | income | transfer) that determines how it affects spending summaries.
- Seed categories are pre-loaded at startup; users can create additional ones.

---

## Data Model

### categories

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| name | text | e.g. "Food & Drink", "Transport" |
| parent_id | uuid nullable → categories.id | for subcategories |
| kind | enum | expense \| income \| transfer |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### categorizations

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| target_type | enum | bank_transaction \| card_transaction |
| target_id | uuid | FK to the respective transaction |
| category_id | uuid → categories.id | |
| source | enum | manual \| rule \| system |
| confidence | float nullable | 0.0–1.0; null for manual |
| rule_id | uuid nullable | FK to category_rules (Cycle 2) |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Unique constraint: `(target_type, target_id)` — one categorization per transaction.

---

## Source Values

| Value | Meaning |
|-------|---------|
| `manual` | User explicitly assigned the category via UI |
| `rule` | Matched by a categorization rule (Cycle 2) |
| `system` | Assigned automatically during import (e.g. transfer detection) |

Manual always wins — if a user manually categorizes a transaction, re-running rules must not overwrite it.

---

## API Endpoints (Cycle 1)

| Method | Path | Description |
|--------|------|-------------|
| GET | /categories | List all categories (tree or flat) |
| POST | /categories | Create a new category |
| PATCH | /categories/{id} | Rename or reparent a category |
| DELETE | /categories/{id} | Delete if unused |
| POST | /categorize | Categorize a single transaction |
| POST | /categorize/bulk | Categorize multiple transactions at once |
| DELETE | /categorizations/{id} | Remove a categorization (uncategorize) |
| GET | /bank-transactions | (existing) — now includes `category_id`, `category_name` in response |
| GET | /card-transactions | (existing) — now includes `category_id`, `category_name` in response |

---

## Future Model (Cycle 2 — Not Implemented Yet)

The rules engine will be added in a later cycle. The schema is planned but not yet created.

### category_rules (planned)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| category_id | uuid → categories.id | |
| match_field | enum | description_raw \| description_norm \| merchant_raw \| amount_minor |
| match_operator | enum | contains \| equals \| regex \| gte \| lte |
| match_value | text | the value to match against |
| target_type | enum | bank_transaction \| card_transaction \| both |
| priority | int | lower = higher priority |
| enabled | bool | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### categorization_events (planned)

Audit log of every categorization change — who/what changed it and when.

---

## Implementation Strategy (Cycle 1)

1. Add `source` column to existing `categorizations` table via Alembic migration.
2. Backfill `source = 'system'` for existing rows where `rule_id IS NULL`.
3. Expose CRUD for categories (`GET/POST/PATCH/DELETE /categories`).
4. Expose `POST /categorize/bulk` for bulk manual categorization.
5. Expose `DELETE /categorizations/{id}` to uncategorize a transaction.
6. Extend `GET /bank-transactions` and `GET /card-transactions` response schemas to include `category_id` and `category_name` via a LEFT JOIN.
7. Frontend: category picker in transaction row (click to assign), bulk select + categorize, filter by category.

Do NOT implement rule evaluation or auto-categorization in Cycle 1.

---

# Next Functional Product Phases

The next stage of product evolution prioritizes major new functional modules before a general polish/refinement cycle.

## Phase 25 — Planning and Control

Goal:
Allow users to define monthly budgets by category and compare planned vs actual spending.

Scope:
- monthly planning periods
- category budgets
- planned vs actual calculations
- remaining budget
- over-budget indicators
- copy previous month budget
- frontend planning page

Out of scope for this phase:
- advanced forecasting
- income planning
- yearly budgets
- AI suggestions

### Data Model

#### budget_periods

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| month | int | 1–12 |
| year | int | e.g. 2026 |
| status | enum | open \| closed |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Unique constraint: `(month, year)` — one period per calendar month.

#### category_budgets

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| budget_period_id | uuid → budget_periods.id | |
| category_id | uuid → categories.id | |
| planned_amount_minor | bigint | stored as integer minor units |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Unique constraint: `(budget_period_id, category_id)` — one budget line per category per period.

### Spending Calculation Rules

- Actual spending for a category = sum of `amount_minor` from `card_transactions` + `bank_transactions` WHERE the transaction has a categorization with that `category_id`.
- Only `expense` kind categories count toward budget consumption.
- `transfer` and `income` categories must be excluded from over-budget calculations.
- Remaining = planned − actual (can be negative when over budget).
- Percentage consumed = actual / planned × 100.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /budgets/periods | List all budget periods (sorted newest first) |
| POST | /budgets/periods | Create a new budget period (month + year) |
| GET | /budgets/{period_id} | Get period with all category budget lines + actuals |
| POST | /budgets/{period_id}/categories | Add or update a category budget line |
| PATCH | /budgets/category-items/{id} | Update planned_amount_minor |
| POST | /budgets/{period_id}/copy-from/{source_period_id} | Copy all budget lines from another period |

### Frontend

- `/planning` page — month selector, summary cards (planned / actual / remaining / % consumed), category budget table with inline editing, over-budget visual indicators.
- Summary cards: planned total, actual total, remaining total, percentage consumed.
- Category table: category name, planned, actual, remaining, progress bar, over-budget badge.
- Inline editing: click planned amount to edit in place.
- Empty state: no budget for selected month → CTA to create budget or copy from previous month.
- Copy-from-previous-month flow: button that triggers POST to copy endpoint.

---

## Phase 26 — Payables and Recurring Expenses

Goal:
Add a lightweight payables and recurring-expense layer.

### First-Cycle Scope

This cycle includes:
- **Manual payables**: user-created payables with monthly occurrences and status tracking (expected → paid/ignored).
- **Recurring detection suggestions**: system analyzes existing transaction history and proposes recurring patterns. User must approve or ignore each suggestion — no auto-approval.

This cycle excludes:
- Full bank reconciliation
- Automatic payment matching
- Invoices / documents / OCR
- Auto-categorization of payable transactions

### Data Model

#### recurring_patterns

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| name | text | human-readable label |
| normalized_description | text | normalized text used for detection |
| category_id | uuid nullable → categories.id | |
| expected_amount_minor | bigint nullable | typical amount in minor units |
| cadence | enum | monthly \| weekly \| yearly \| custom |
| detection_source | enum | system \| manual |
| status | enum | suggested \| approved \| ignored |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### payables

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| name | text | |
| category_id | uuid nullable → categories.id | |
| default_amount_minor | bigint nullable | |
| notes | text nullable | |
| source_type | enum | manual \| recurring_pattern |
| recurring_pattern_id | uuid nullable → recurring_patterns.id | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### payable_occurrences

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| payable_id | uuid → payables.id | |
| due_date | date | |
| expected_amount_minor | bigint | |
| actual_amount_minor | bigint nullable | set when marked as paid |
| status | enum | expected \| pending \| paid \| ignored |
| notes | text nullable | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### Recurring Detection Heuristics

- Scan `bank_transactions` and `card_transactions` for normalized descriptions that appear 2+ times across different calendar months.
- Group by normalized description; count distinct months; compute median amount.
- Infer cadence from inter-occurrence gaps (≈30 days → monthly, ≈7 days → weekly, ≈365 days → yearly).
- Only generate a suggestion if confidence threshold is met (≥3 occurrences, consistent cadence).
- All system-detected patterns start with `status = 'suggested'` — never auto-approved.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /recurring-patterns | List patterns (filter: status) |
| POST | /recurring-patterns/detect | Trigger detection scan, returns new suggestions |
| POST | /recurring-patterns/{id}/approve | Approve a suggested pattern |
| POST | /recurring-patterns/{id}/ignore | Ignore a suggested pattern |
| GET | /payables | List payables |
| POST | /payables | Create manual payable |
| GET | /payable-occurrences | List occurrences (filter: month, year, status) |
| POST | /payable-occurrences/generate | Generate occurrences for a given month/year from approved payables |
| PATCH | /payable-occurrences/{id} | Update status (paid/ignored) and actual_amount_minor |

### Frontend

- `/payables` page — current month occurrences table, filter by status, mark paid/ignored, create manual payable.
- `/recurring` page or section — list suggested patterns with example transactions, approve/ignore actions.
- Sidebar entries: "Payables" and "Recurring" under a new "Control" nav group.

---

## Phase 27 — Investments

Goal: Add manual investment tracking and portfolio visibility. First version is manual-only — no brokerage integrations or automatic price sync.

### Supported Asset Classes
`stock` | `bond` | `etf` | `real_estate` | `crypto` | `cash` | `other`

### Data Model

#### investment_accounts
Represents a brokerage or custody account.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| name | text | display name |
| institution_name | text nullable | e.g. "XP", "BTG" |
| currency | char(3) | ISO currency code |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### assets
Represents a tradable instrument.

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| symbol | varchar(20) nullable | ticker e.g. "PETR4" |
| name | text | full name |
| asset_class | enum | stock/bond/etf/real_estate/crypto/cash/other |
| currency | char(3) | |
| metadata | jsonb nullable | extra data |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### asset_positions
One position per account+asset (quantity + value snapshot).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| investment_account_id | uuid → investment_accounts.id CASCADE | |
| asset_id | uuid → assets.id | |
| quantity | float | fractional units supported |
| average_cost_minor | bigint nullable | average purchase price in minor units |
| current_value_minor | bigint nullable | current market value in minor units |
| as_of_date | date | when this snapshot was recorded |
| created_at | timestamptz | |
| updated_at | timestamptz | |

#### portfolio_snapshots
Point-in-time portfolio total (for future trend tracking).

| Column | Type | Notes |
|--------|------|-------|
| id | uuid pk | |
| snapshot_date | date | |
| total_value_minor | bigint | |
| currency | char(3) | |
| notes | text nullable | |
| created_at | timestamptz | |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /investment-accounts | List all accounts |
| POST | /investment-accounts | Create account |
| GET | /assets | List all assets |
| POST | /assets | Create asset |
| GET | /asset-positions | List positions (filter: investment_account_id) |
| POST | /asset-positions | Add position |
| PATCH | /asset-positions/{id} | Update quantity/value/date |
| GET | /portfolio/summary | Portfolio totals + allocation by asset class |

### Portfolio Summary Logic
- Sum `current_value_minor` per account → `accounts[]`
- Sum `current_value_minor` per asset class → `allocation[]` with percentage
- Grand total = sum of all `current_value_minor` values (null treated as 0)

### Frontend
- `/investments` page — summary cards (total, positions count, asset classes), allocation bar chart, per-account positions table with edit buttons
- Add Account dialog, Add Asset dialog, Add Position dialog, Update Position dialog
- Empty state with CTA when no accounts exist
- "Investments" added to Sidebar nav under "Control" group

Out of scope for this phase:
- Brokerage integrations / API sync
- Automatic market price updates
- Tax calculations / IRR / performance analytics
- Snapshot creation via API