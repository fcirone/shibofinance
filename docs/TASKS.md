# Shibo Finance — Execution Plan

Progress legend: `[ ]` pending · `[x]` done

## Execution Rules
- Execute ONLY the next unchecked task.
- Do not change completed code unless required to complete the current task.
- If a spec mismatch is found, propose a minimal patch and stop.
- Always add or update tests for the current task.
- Do not start a new phase before the current phase is complete.
- Update documentation before coding when a new major phase starts.

---

## Phase 1 — Repo Skeleton

- [x] 1.1 Create root directory structure (`apps/`, `packages/`, `tools/`, `data/`)
- [x] 1.2 Add `.gitignore` (Python, Docker, `.env`)
- [x] 1.3 Add `.env.example` with required env vars
- [x] 1.4 Create root `Makefile` with `up`, `down`, `logs`, `migrate`, `test`, `api-shell` targets
- [x] 1.5 Create `README.md` with setup instructions

---

## Phase 2 — Docker Compose

- [x] 2.1 Write `docker-compose.yml` with `db` (postgres:16) and `api` (FastAPI) services
- [x] 2.2 Add optional `pgadmin` service
- [x] 2.3 Write `apps/api/Dockerfile`
- [x] 2.4 Confirm `make up` starts the full stack

---

## Phase 3 — Database Models

- [x] 3.1 Create `apps/api/pyproject.toml` (Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, Pytest)
- [x] 3.2 Implement `app/settings.py` (env-based config)
- [x] 3.3 Implement `app/db.py` (SQLAlchemy async engine + session factory)
- [x] 3.4 Implement `app/models.py` with all tables:
  - [x] 3.4.1 `instruments`
  - [x] 3.4.2 `credit_cards`
  - [x] 3.4.3 `import_batches`
  - [x] 3.4.4 `bank_transactions`
  - [x] 3.4.5 `credit_card_statements`
  - [x] 3.4.6 `credit_card_transactions`
  - [x] 3.4.7 `statement_payment_links`
  - [x] 3.4.8 `categories`
  - [x] 3.4.9 `categorizations`

---

## Phase 4 — Alembic Migrations

- [x] 4.1 Configure `apps/api/alembic.ini`
- [x] 4.2 Configure `apps/api/alembic/env.py` (async-compatible, reads `DATABASE_URL` from env)
- [x] 4.3 Generate initial migration from models
- [x] 4.4 Confirm `make migrate` applies migrations cleanly against running Postgres

---

## Phase 5 — Core Packages

- [x] 5.1 `packages/core/money.py` — integer minor-unit conversion helpers
- [x] 5.2 `packages/core/timezones.py` — timezone constants and UTC conversion
- [x] 5.3 `packages/core/normalizers.py` — description normalization (lowercase, remove accents, collapse whitespace, remove duplicate punctuation)
- [x] 5.4 `packages/core/fingerprint.py` — SHA256 fingerprint generation from `(instrument_id, posted_date, currency, amount_minor, description_norm)`

---

## Phase 6 — Importer Framework

- [x] 6.1 Define `packages/importers/base.py` — `BaseImporter` interface (`SOURCE_NAME`, `detect()`, `parse()`) and `ImportResult` dataclass
- [x] 6.2 Implement `packages/importers/registry.py` — auto-detects importer from file bytes + filename
- [x] 6.3 Implement `apps/api/services/fingerprint_service.py` — wraps core fingerprint logic
- [x] 6.4 Implement `apps/api/services/dedupe_service.py` — upsert logic using `fingerprint_hash` / `source_tx_id`
- [x] 6.5 Implement `apps/api/services/import_service.py` — orchestrates full import pipeline (detect → parse → normalize → fingerprint → upsert → statement → match)

---

## Phase 7 — Santander Brazil Importer

- [x] 7.1 `packages/importers/santander_br/detector.py` — detect Santander BR files
- [x] 7.2 `packages/importers/santander_br/bank_parser_pdf.py` — parse bank statement PDF (spec was PDF, not CSV)
- [x] 7.3 `packages/importers/santander_br/card_parser_pdf.py` — parse credit card PDF
- [x] 7.4 Add sample files to `data/samples/santander_br/`
- [x] 7.5 Write and run tests — 16/16 passing (`tests/test_santander_br.py`)

---

## Phase 8 — Statement Payment Matching

- [x] 8.1 Implement `apps/api/services/statement_matcher.py`
  - [x] 8.1.1 Detect payment patterns: `PAGAMENTO FATURA`, `PAGTO CARTAO`, `CARD PAYMENT`
  - [x] 8.1.2 Match by amount (exact or partial) and date proximity to statement due date
  - [x] 8.1.3 Insert record into `statement_payment_links`
  - [x] 8.1.4 Auto-categorize matched bank transaction as `transfer`

---

## Phase 9 — API Endpoints

- [x] 9.1 `app/main.py` — FastAPI app setup, router registration
- [x] 9.2 `app/schemas.py` — Pydantic v2 request/response schemas
- [x] 9.3 `app/routers/health.py` — `GET /health`
- [x] 9.4 `app/routers/instruments.py` — `POST /instruments`, `GET /instruments`
- [x] 9.5 `app/routers/imports.py` — `POST /imports/upload`
- [x] 9.6 `app/routers/bank_transactions.py` — `GET /bank-transactions`
- [x] 9.7 `app/routers/card_transactions.py` — `GET /card-transactions`
- [x] 9.8 `app/routers/statements.py` — `GET /card-statements`
- [x] 9.9 `app/routers/categories.py` — `GET /categories`, `POST /categorize`
- [x] 9.10 `app/routers/spending_summary.py` — `GET /spending-summary` (card txs + bank txs excluding transfers)

---

## Phase 10 — CLI Tool

- [x] 10.1 Implement `tools/import_cli.py`
  - [x] 10.1.1 `import` command (`--file`, `--instrument`, `--source auto`)
  - [x] 10.1.2 `list-transactions` command (`--instrument`)

---

## Phase 11 — Tests

- [x] 11.1 `tests/test_health.py` — health endpoint returns 200
- [x] 11.2 `tests/test_import_idempotency.py` — reimporting same file produces no new rows
- [x] 11.3 Fingerprint consistency test — same input always produces same hash
- [x] 11.4 Basic query test — imported transactions appear in GET endpoints
- [x] 11.5 Confirm `make test` passes with all tests green

---

## Phase 12 — XP Brazil Importer

- [x] 12.1 `packages/importers/xp_br/detector.py`
- [x] 12.2 `packages/importers/xp_br/bank_parser_pdf.py` (PDF, not CSV — spec updated)
- [x] 12.3 `packages/importers/xp_br/card_parser_pdf.py` (PDF, not CSV — spec updated)
- [x] 12.4 Add sample files to `data/samples/xp_br/`
- [x] 12.5 Write and run tests — 21/21 passing (`tests/test_xp_br.py`)

---

## Phase 13 — BBVA Uruguay Importer

- [x] 13.1 `packages/importers/bbva_uy/detector.py`
- [x] 13.2 `packages/importers/bbva_uy/bank_parser_pdf.py` (PDF, not CSV — bank statement is a PDF)
- [x] 13.3 `packages/importers/bbva_uy/card_parser_pdf.py`
- [x] 13.4 Add sample files to `data/samples/bbva_uy/`
- [x] 13.5 Write and run tests — 24/24 passing (`tests/test_bbva_uy.py`)

---

## Backend Acceptance Checklist

- [x] `docker compose up` starts the full system
- [x] API is reachable at `http://localhost:8000`
- [x] Can create instruments via `POST /instruments`
- [x] Can upload a CSV/PDF via `POST /imports/upload`
- [x] Transactions appear in `GET /bank-transactions` or `GET /card-transactions`
- [x] Re-importing the same file produces zero new rows (idempotency)
- [x] `GET /spending-summary` returns correct totals
- [x] 117 tests passing (`make test`)

---

## Phase 14 — Backend Additions for Frontend

> Minimal read-only additions to expose already-existing data. Do NOT change models or migrations.

- [x] 14.1 Add CORS middleware to `apps/api/app/main.py` — allow `http://localhost:3000` (and env-configurable origins)
- [x] 14.2 Add `GET /imports` endpoint (`apps/api/app/routers/imports.py`) — list import batches; params: `instrument_id` (optional), `limit` (default 50), `offset` (default 0); response: `list[ImportBatchOut]`
- [x] 14.3 Add `GET /imports/{batch_id}` endpoint — single batch detail; response: `ImportBatchOut`; 404 if not found
- [x] 14.4 Write tests for new endpoints (added to `tests/test_api.py`)
- [x] 14.5 Confirm `make test` still passes with all tests green — 117/117 passing

**Acceptance:** `GET /imports` returns paginated list of batches. `GET /imports/{id}` returns single batch or 404. CORS allows requests from localhost:3000.

---

## Phase 15 — Web Service Scaffold

- [x] 15.1 Create `apps/web/` with `npx create-next-app@latest` — App Router, TypeScript, Tailwind CSS
- [x] 15.2 Install dependencies: `shadcn/ui` (init), `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers`, `recharts`, `openapi-typescript`, `lucide-react`, `sonner`
- [x] 15.3 Run `npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts` — generate API types
- [x] 15.4 Create `apps/web/src/lib/api.ts` — typed API client wrapping `fetch`; reads `NEXT_PUBLIC_API_BASE_URL`; throws `ApiError` on non-2xx
- [x] 15.5 Create `apps/web/src/lib/utils.ts` — `formatAmount(minor, currency)`, `formatDate(date)`, `formatDateTime` helpers
- [x] 15.6 Create `apps/web/src/lib/query-client.ts` — TanStack Query client singleton
- [x] 15.7 Create `apps/web/Dockerfile` — Node 22 alpine, hot-reload dev server
- [x] 15.8 Update `docker-compose.yml` — add `web` service (port 3000, volume mounts)
- [x] 15.9 Add Makefile targets: `web-dev`, `web-build`, `web-lint`, `web-types`
- [x] 15.10 Verify `make up` starts web at `http://localhost:3000` and API is reachable from browser — ✓ 200 OK, CORS confirmed

**Acceptance:** Next.js dev server starts. `/api-types.ts` has typed interfaces matching backend schemas. `apiFetch("/health")` returns `{status: "ok"}`.

---

## Phase 16 — AppShell & Core Layout

- [x] 16.1 Create `AppShell` component — sidebar + topbar wrapper layout
- [x] 16.2 Create `Sidebar` — nav links: Dashboard, Instruments, Import, Import History, Transactions, Statements; active state; collapse to icons on `lg`
- [x] 16.3 Create `Topbar` — hamburger for mobile (Sheet), desktop collapse toggle
- [x] 16.4 Wrap root `layout.tsx` with `QueryClientProvider` + `Toaster` (Sonner) + Inter font
- [x] 16.5 Create `EmptyState` component — icon prop, title, description, optional CTA button
- [x] 16.6 Create `LoadingSkeleton` — generic + `CardSkeleton` + `TableSkeleton` variants
- [x] 16.7 Create `PageHeader` component — title + optional right-side action
- [x] 16.8 Create `ImportStatusBadge` / `StatementStatusBadge` — color-coded per status
- [x] 16.9 Create `SourceBadge` — santander_br / xp_br / bbva_uy color-coded
- [x] 16.10 Create `AmountDisplay` — formats minor units + currency; red if negative

**Acceptance:** Navigating between pages shows correct sidebar active state. AppShell renders on all pages. Components render in Storybook or a test page without errors.

---

## Phase 17 — Instruments Page

- [x] 17.1 Create `useInstruments` hook — `GET /instruments`, `staleTime: 30_000`
- [x] 17.2 Create `InstrumentCard` component — name, type badge, source badge, currency, created date
- [x] 17.3 Create `InstrumentPicker` component — searchable `<Select>` populated from `useInstruments`; accepts optional `typeFilter` prop
- [x] 17.4 Create `CreateInstrumentDialog` — shadcn `Dialog` with RHF + Zod form; all fields; `POST /instruments` on submit; invalidates query; toast on error
- [x] 17.5 Create `EditInstrumentDialog` — prefills name + metadata; `PATCH /instruments/{id}` on submit
- [x] 17.6 Create `/instruments` page — responsive grid, `LoadingSkeleton`, `EmptyState`, both dialogs
- [x] 17.7 Metadata JSON field: validated with Zod refine + `JSON.parse`; inline error shown

**Acceptance:** Can create a new instrument from the UI. Instrument appears in list immediately (optimistic or after invalidation). Edit updates name/metadata. Empty state shown when no instruments exist.

---

## Phase 18 — Import Pages

- [x] 18.1 Create `useImports` hook — `GET /imports?instrument_id=…&limit=50&offset=…`
- [x] 18.2 Create `ImportBatchCard` — filename, instrument name (lookup from instruments list), status badge, inserted/dup/error counts, formatted date
- [x] 18.3 Create `BatchDetailDrawer` — shadcn `Sheet`; shows full batch metadata; "View transactions" link; triggered by clicking `ImportBatchCard`
- [x] 18.4 Create `/imports` page — `InstrumentPicker` filter (all instruments); list of `ImportBatchCard`; "Load more" pagination; `EmptyState` when no batches
- [x] 18.5 Create `UploadDropzone` component — native drag-and-drop; accepted types: `.pdf`, `.csv`; max 20 MB; shows file name + size after pick; clear button
- [x] 18.6 Create `/import/new` page — `InstrumentPicker` (required) + `UploadDropzone`; "Import File" submit button; calls `POST /imports/upload`; on success shows `ImportBatchCard` with result; on error shows error toast + inline message
- [x] 18.7 Upload progress: show spinner/progress bar during upload; disable submit during in-flight request

**Acceptance:** Can upload a PDF/CSV via UI. Result card shows inserted/duplicate/error counts. Import appears in `/imports` history. Selecting an instrument in history filters the list.

---

## Phase 19 — Transactions Page

- [x] 19.1 Create `useBankTransactions` hook — `GET /bank-transactions?…`; params: instrument_id, date_from, date_to, limit, offset
- [x] 19.2 Create `useCardTransactions` hook — `GET /card-transactions?…`; same params
- [x] 19.3 Create `TransactionFilters` component — `InstrumentPicker` + date inputs + text search input; all values sync to URL search params
- [x] 19.4 Create `TransactionsTable` — shadcn `Table`; columns differ by type (bank vs card); `AmountDisplay` in amount cell; installment badge for card
- [x] 19.5 Create `PaginationBar` — previous/next + page info; wired to offset param
- [x] 19.6 Create `/transactions` page — tab bar Bank / Card; `TransactionFilters`; `TransactionsTable` with `PaginationBar`; `TableSkeleton` (8 rows); `EmptyState` when no results
- [x] 19.7 Text search: client-side filter on `description_raw` within the current page
- [x] 19.8 Filter state in URL: `?tab=bank&instrument_id=…&date_from=…&date_to=…&page=2`

**Acceptance:** Transactions load with pagination (50/page). Instrument + date filters work. Tab switches between bank and card. Empty state shown when no results. URL reflects filter state (shareable/bookmarkable).

---

## Phase 20 — Statements Page

- [x] 20.1 Create `useStatements` hook — `GET /card-statements?instrument_id=…`
- [x] 20.2 Create `StatementCard` — period range, due date, total (`AmountDisplay`), status badge
- [x] 20.3 Create `StatementDetailDrawer` — shadcn `Sheet`; statement metadata; "View transactions" link → `/transactions?tab=card&instrument_id=…&date_from=…&date_to=…`
- [x] 20.4 Create `/statements` page — `InstrumentPicker` (credit_card type only); list of `StatementCard`; `LoadingSkeleton`; `EmptyState`
- [x] 20.5 Sort statements newest-first by `statement_end`

**Acceptance:** Statements list filtered by card instrument. "View transactions" link opens transactions page pre-filtered to that statement's date range.

---

## Phase 21 — Dashboard

- [x] 21.1 Create `useSpendingSummary` hook — `GET /spending-summary?date_from=…&date_to=…`; default to current calendar month
- [x] 21.2 Create `SummaryCards` — 3 stat cards: Total Expenses (current month), Total Transactions, Last Import date; `LoadingSkeleton` per card
- [x] 21.3 Create `SpendingChart` — Recharts `BarChart` (horizontal) or `PieChart`; categories on y-axis; amounts on x-axis; "Uncategorized" bucket at bottom; empty state if no data
- [x] 21.4 Create `RecentImportsWidget` — last 5 batches (`GET /imports?limit=5`); compact list; "View all" link
- [x] 21.5 Create QuickActions section — two `Card` CTAs: "Import a statement" → `/import/new`, "View transactions" → `/transactions`
- [x] 21.6 Create `/` (Dashboard) page — month picker in topbar; `SummaryCards` + `SpendingChart` + `RecentImportsWidget` + `QuickActions`
- [x] 21.7 Full-page `EmptyState` (onboarding) when no instruments exist — step list: Add instrument → Import file → View data

**Acceptance:** Dashboard loads with current month spending summary. Chart renders. Recent imports show. Quick actions navigate correctly. Empty/onboarding state shown on first run.

---

## Phase 22 — UI Polish & Accessibility

- [x] 22.1 Add `LoadingSkeleton` to every page and component that fetches data (audit all pages)
- [x] 22.2 Add `EmptyState` to every list view (audit all pages)
- [x] 22.3 Verify all error cases show toast with informative message (network error, 422, 404, 500)
- [x] 22.4 Responsive audit: test all pages at 375px (mobile), 768px (tablet), 1280px (desktop)
- [x] 22.5 Mobile nav: hamburger opens sidebar as a `Sheet` overlay
- [x] 22.6 Accessibility audit: keyboard navigation through all forms and tables; ARIA labels on icon-only buttons; focus ring visible
- [x] 22.7 Color contrast: verify all text passes WCAG AA (4.5:1 for normal, 3:1 for large)
- [x] 22.8 Consistent spacing pass: verify `p-6` page padding, `gap-4` card grids, `space-y-6` sections across all pages

**Acceptance:** All pages usable on mobile. No layout shift on load. Keyboard-navigable. All errors surfaced via toast. Skeletons match content shape.

---

---

## Phase 23 — Categorization (Cycle 1)

> Manual categorization via UI. No rules engine. No auto-categorization.

### Backend

- [x] 23.1 Add `source` column (`manual | rule | system`) to `categorizations` via Alembic migration; backfill existing rows with `source = 'system'`
- [x] 23.2 Verify `categories` and `categorizations` tables match documented schema; adjust if needed
- [x] 23.3 Seed default categories on startup (Food & Drink, Transport, Shopping, Health, Housing, Entertainment, Travel, Income, Transfer)
- [x] 23.4 `GET /categories` — return flat list with optional `?kind=expense|income|transfer` filter; include `parent_id` and `kind`
- [x] 23.5 `POST /categories` — create category; validate name uniqueness within same parent
- [x] 23.6 `PATCH /categories/{id}` — rename or reparent; reject if would create circular parent chain
- [x] 23.7 `DELETE /categories/{id}` — reject if category has active categorizations
- [x] 23.8 `POST /categorize` (existing) — update to set `source = 'manual'`; upsert on `(target_type, target_id)`
- [x] 23.9 `POST /categorize/bulk` — accept list of `{target_type, target_id, category_id}`; set `source = 'manual'`; return count
- [x] 23.10 `DELETE /categorizations/{id}` — remove a categorization (uncategorize); 404 if not found
- [x] 23.11 Extend `GET /bank-transactions` response to include `category_id` (nullable) and `category_name` (nullable) via LEFT JOIN
- [x] 23.12 Extend `GET /card-transactions` response to include `category_id` (nullable) and `category_name` (nullable) via LEFT JOIN
- [x] 23.13 Update OpenAPI schema and regenerate `api-types.ts` on frontend
- [x] 23.14 Write tests: category CRUD, bulk categorize, uncategorize, transaction responses include category fields

### Frontend

- [x] 23.15 Create `useCategories` hook — `GET /categories`; `staleTime: 30_000`
- [x] 23.16 Create `CategoryBadge` component — compact pill showing category name; muted if uncategorized
- [x] 23.17 Create `CategoryPicker` component — searchable `<Select>` of categories grouped by kind; "None" option to uncategorize
- [x] 23.18 Add category column to `TransactionsTable` (bank + card) — shows `CategoryBadge`; clicking opens `CategoryPicker` inline
- [x] 23.19 Implement inline categorization — clicking a row's category cell opens `CategoryPicker`; on select calls `POST /categorize`; invalidates query
- [x] 23.20 Add category filter to `TransactionFilters` — `CategoryPicker` with `allowAll`; syncs to `?category_id=` URL param; pass to API query
- [x] 23.21 Create bulk categorization — checkbox column in `TransactionsTable`; "Categorize N selected" action bar appears when rows are checked; calls `POST /categorize/bulk`
- [x] 23.22 Create `/categories` page — list of all categories with kind badge; inline rename; delete (disabled if in use); "Add category" form
- [x] 23.23 Add "Categories" link to Sidebar nav

**Acceptance:** User can click any transaction row to assign a category. Bulk selection + categorize works. Category filter narrows the list. `/categories` page shows all categories with CRUD.

---

## Phase 24 — Categorization Rules (Cycle 2)

> Automated rule-based categorization. Builds on Cycle 1. Do not implement until Cycle 1 is complete and verified.

- [x] 24.1 Add `category_rules` table via Alembic migration (match_field, match_operator, match_value, target_type, priority, enabled)
- [x] 24.2 Add `categorization_events` audit log table
- [x] 24.3 Implement rule evaluation engine — ordered by priority; first match wins; skips `source = 'manual'` transactions
- [x] 24.4 `GET /category-rules` — list rules with category name
- [x] 24.5 `POST /category-rules` — create rule; validate match_field + match_operator combination
- [x] 24.6 `PATCH /category-rules/{id}` — update rule; toggle enabled
- [x] 24.7 `DELETE /category-rules/{id}` — delete rule
- [x] 24.8 `POST /category-rules/dry-run` — apply rules to all uncategorized transactions without saving; return preview count per category
- [x] 24.9 `POST /category-rules/apply` — run rule engine on all uncategorized transactions; return applied count
- [x] 24.10 Hook rule engine into import pipeline — run after upsert, before returning result
- [x] 24.11 Frontend: rules management page (`/categories/rules`)
- [x] 24.12 Frontend: "Apply to similar" button on categorized transaction — pre-fills a rule with the transaction's description
- [x] 24.13 Frontend: dry-run preview before applying rules
- [x] 24.14 Frontend: show rule name in category badge tooltip when `source = 'rule'`

## Phase 25 — Planning and Control

### 25.1 Documentation
- [x] Update CLAUDE.md with a new "Planning and Control" section
- [x] Update ROADMAP.md if needed
- [x] Confirm scope for this phase is monthly category budgeting only

**Acceptance criteria**
- Product documentation reflects the new Planning and Control module
- Scope is clearly limited to monthly category-based budgeting

---

### 25.2 Backend Data Model
- [x] Create `budget_periods` table
- [x] Create `category_budgets` table
- [x] Add migrations
- [x] Define constraints to avoid duplicate category budgets for the same period

Suggested model:

`budget_periods`
- id
- month
- year
- status (open | closed)
- created_at
- updated_at

`category_budgets`
- id
- budget_period_id
- category_id
- planned_amount_minor
- created_at
- updated_at

**Acceptance criteria**
- Database supports monthly planning by category
- No duplicate budget records for the same category and period

---

### 25.3 Backend Services
- [x] Implement service to calculate actual spending by category for a given budget period
- [x] Exclude transfer categories from expense budget calculations
- [x] Return planned, actual, remaining and percentage consumed

**Acceptance criteria**
- Service returns correct values using categorized transactions

---

### 25.4 Backend API
- [x] GET `/budgets/periods`
- [x] POST `/budgets/periods`
- [x] GET `/budgets/{period_id}`
- [x] POST `/budgets/{period_id}/categories`
- [x] PATCH `/budgets/category-items/{id}`
- [x] POST `/budgets/{period_id}/copy-from/{source_period_id}`

**Acceptance criteria**
- API allows creating, editing and copying monthly budgets

---

### 25.5 Frontend Pages
- [x] Create `/planning` page
- [x] Add month selector
- [x] Show budget summary cards:
  - planned total
  - actual total
  - remaining total
  - percentage consumed
- [x] Show category budget table
- [x] Allow inline planned amount editing
- [x] Add visual status for:
  - within budget
  - near limit
  - over budget

**Acceptance criteria**
- User can create and manage a monthly budget from the UI

---

### 25.6 Frontend UX
- [x] Add empty state for month with no budget
- [x] Add create-first-budget CTA
- [x] Add copy-from-previous-month flow
- [x] Add loading and error states

**Acceptance criteria**
- Planning UX is usable and understandable without documentation

---

### 25.7 Tests
- [x] Add backend tests for budget calculations
- [x] Add backend tests for copy-from-period

**Acceptance criteria**
- Budget module is tested and stable

---

## Phase 26 — Payables and Recurring Expenses

### 26.1 Documentation
- [ ] Update CLAUDE.md with a new "Payables and Recurring Expenses" section
- [ ] Document that first cycle includes manual payables + recurring detection suggestions
- [ ] Keep automatic reconciliation out of scope for this phase

**Acceptance criteria**
- Documentation clearly defines the module scope

---

### 26.2 Backend Data Model
- [ ] Create `recurring_patterns` table
- [ ] Create `payables` table
- [ ] Create `payable_occurrences` table
- [ ] Add migrations

Suggested model:

`recurring_patterns`
- id
- name
- normalized_description
- category_id nullable
- expected_amount_minor nullable
- cadence (monthly | weekly | yearly | custom)
- detection_source (system | manual)
- status (suggested | approved | ignored)
- created_at
- updated_at

`payables`
- id
- name
- category_id nullable
- default_amount_minor nullable
- notes nullable
- source_type (manual | recurring_pattern)
- recurring_pattern_id nullable
- created_at
- updated_at

`payable_occurrences`
- id
- payable_id
- due_date
- expected_amount_minor
- actual_amount_minor nullable
- status (expected | pending | paid | ignored)
- notes nullable
- created_at
- updated_at

**Acceptance criteria**
- Database supports recurring patterns and monthly payable items

---

### 26.3 Backend Detection Logic
- [ ] Implement recurring transaction detection heuristics
- [ ] Detect likely recurring expenses from transaction history
- [ ] Generate suggested recurring patterns
- [ ] Avoid auto-approving system-detected patterns

**Acceptance criteria**
- System can produce recurring suggestions from existing data

---

### 26.4 Backend API
- [ ] GET `/recurring-patterns`
- [ ] POST `/recurring-patterns/{id}/approve`
- [ ] POST `/recurring-patterns/{id}/ignore`
- [ ] GET `/payables`
- [ ] POST `/payables`
- [ ] GET `/payable-occurrences`
- [ ] POST `/payable-occurrences/generate`
- [ ] PATCH `/payable-occurrences/{id}`

**Acceptance criteria**
- API supports recurring review and payables management

---

### 26.5 Frontend Pages
- [ ] Create `/payables` page
- [ ] Show current month payable occurrences
- [ ] Allow filtering by status
- [ ] Allow marking payable occurrence as paid or ignored
- [ ] Allow manual payable creation

**Acceptance criteria**
- User can manage monthly payables in UI

---

### 26.6 Frontend Recurring Suggestions
- [ ] Create `/recurring` page or section
- [ ] Show suggested recurring patterns
- [ ] Allow approve / ignore
- [ ] Show source examples used for detection

**Acceptance criteria**
- User can review recurring suggestions without ambiguity

---

### 26.7 Tests
- [ ] Add backend tests for recurring detection heuristics
- [ ] Add backend tests for occurrence generation
- [ ] Add frontend smoke tests for payables pages

**Acceptance criteria**
- Payables module is tested and stable

---

## Phase 27 — Investments

### 27.1 Documentation
- [ ] Update CLAUDE.md with a new "Investments" section
- [ ] Document that first version is manual-only
- [ ] Document supported asset classes

**Acceptance criteria**
- Investments scope is clear and limited

---

### 27.2 Backend Data Model
- [ ] Create `investment_accounts` table
- [ ] Create `assets` table
- [ ] Create `asset_positions` table
- [ ] Create `portfolio_snapshots` table
- [ ] Add migrations

Suggested model:

`investment_accounts`
- id
- name
- institution_name nullable
- currency
- created_at
- updated_at

`assets`
- id
- symbol nullable
- name
- asset_class
- currency
- metadata nullable
- created_at
- updated_at

`asset_positions`
- id
- investment_account_id
- asset_id
- quantity
- average_cost_minor nullable
- current_value_minor nullable
- as_of_date
- created_at
- updated_at

`portfolio_snapshots`
- id
- snapshot_date
- total_value_minor
- currency
- notes nullable
- created_at

**Acceptance criteria**
- Database supports manual investment portfolio tracking

---

### 27.3 Backend Services
- [ ] Implement allocation summary by asset class
- [ ] Implement account-level and portfolio-level totals
- [ ] Implement current portfolio summary endpoint

**Acceptance criteria**
- Backend can return portfolio summary and allocation breakdown

---

### 27.4 Backend API
- [ ] GET `/investment-accounts`
- [ ] POST `/investment-accounts`
- [ ] GET `/assets`
- [ ] POST `/assets`
- [ ] GET `/asset-positions`
- [ ] POST `/asset-positions`
- [ ] PATCH `/asset-positions/{id}`
- [ ] GET `/portfolio/summary`

**Acceptance criteria**
- API supports manual investment tracking flows

---

### 27.5 Frontend Pages
- [ ] Create `/investments` page
- [ ] Show total invested value
- [ ] Show allocation by asset class
- [ ] Show list of positions
- [ ] Allow manual asset and position creation
- [ ] Allow updating current position values

**Acceptance criteria**
- User can track a manual portfolio from the UI

---

### 27.6 Frontend UX
- [ ] Add empty states for no investment accounts
- [ ] Add onboarding CTA for first asset
- [ ] Add loading and error states

**Acceptance criteria**
- Investments module is usable for first-time setup

---

### 27.7 Tests
- [ ] Add backend tests for portfolio summary
- [ ] Add frontend smoke tests for investments page

**Acceptance criteria**
- Investments module is tested and stable

**Acceptance:** Rules auto-categorize matching transactions on import. Manual categorizations are never overwritten by rules. Dry-run shows preview before committing.

---

## Frontend Acceptance Checklist (Cycle 1)

- [ ] `make up` starts web at `http://localhost:3000` alongside API + DB
- [ ] Can create an instrument via UI
- [ ] Can upload a PDF/CSV and see inserted/dup/error counts
- [ ] Import appears in history list
- [ ] Transactions load with pagination and instrument/date filters
- [ ] Card statements list with totals and status
- [ ] Dashboard shows spending summary for current month
- [ ] All pages have loading skeletons and empty states
- [ ] Error toasts shown on API failures
- [ ] Responsive on mobile (375px)
