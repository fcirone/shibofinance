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