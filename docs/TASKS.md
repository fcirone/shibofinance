# Finance OS — Execution Plan

Progress legend: `[ ]` pending · `[x]` done

## Execution Rules
- Execute ONLY the next unchecked task.
- Do not change completed code unless required to complete the current task.
- If a spec mismatch is found, propose a minimal patch and stop.
- Always add/adjust tests for the current task.

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

- [ ] 17.1 Create `useInstruments` hook — `GET /instruments`, `staleTime: 30_000`
- [ ] 17.2 Create `InstrumentCard` component — name, type badge, source badge, currency, created date
- [ ] 17.3 Create `InstrumentPicker` component — searchable `<Select>` populated from `useInstruments`; accepts optional `typeFilter` prop
- [ ] 17.4 Create `CreateInstrumentDialog` — shadcn `Dialog` with RHF + Zod form; fields: name, type, source, currency, source_instrument_id, metadata (JSON textarea); `POST /instruments` on submit; invalidates instruments query on success; toast on error
- [ ] 17.5 Create `EditInstrumentDialog` — prefills name + metadata; `PATCH /instruments/{id}` on submit
- [ ] 17.6 Create `/instruments` page — grid of `InstrumentCard`; "Add Instrument" button in `PageHeader`; `LoadingSkeleton` while loading; `EmptyState` when empty
- [ ] 17.7 Metadata JSON field: validate `JSON.parse` in Zod; show inline error if invalid JSON

**Acceptance:** Can create a new instrument from the UI. Instrument appears in list immediately (optimistic or after invalidation). Edit updates name/metadata. Empty state shown when no instruments exist.

---

## Phase 18 — Import Pages

- [ ] 18.1 Create `useImports` hook — `GET /imports?instrument_id=…&limit=50&offset=…`
- [ ] 18.2 Create `ImportBatchCard` — filename, instrument name (lookup from instruments list), status badge, inserted/dup/error counts, formatted date
- [ ] 18.3 Create `BatchDetailDrawer` — shadcn `Sheet`; shows full batch metadata; "View transactions" link; triggered by clicking `ImportBatchCard`
- [ ] 18.4 Create `/imports` page — `InstrumentPicker` filter (all instruments); list of `ImportBatchCard`; "Load more" pagination; `EmptyState` when no batches
- [ ] 18.5 Create `UploadDropzone` component — `react-dropzone` or native drag-and-drop; accepted types: `.pdf`, `.csv`; max 20 MB; shows file name + size after pick; clear button
- [ ] 18.6 Create `/import/new` page — `InstrumentPicker` (required) + `UploadDropzone`; "Import File" submit button; calls `POST /imports/upload`; on success shows `ImportBatchCard` with result; on error shows error toast + inline message
- [ ] 18.7 Upload progress: show spinner/progress bar during upload; disable submit during in-flight request

**Acceptance:** Can upload a PDF/CSV via UI. Result card shows inserted/duplicate/error counts. Import appears in `/imports` history. Selecting an instrument in history filters the list.

---

## Phase 19 — Transactions Page

- [ ] 19.1 Create `useBankTransactions` hook — `GET /bank-transactions?…`; params: instrument_id, date_from, date_to, limit, offset
- [ ] 19.2 Create `useCardTransactions` hook — `GET /card-transactions?…`; same params
- [ ] 19.3 Create `TransactionFilters` component — `InstrumentPicker` + `DateRangePicker` + text search input; all values sync to URL search params
- [ ] 19.4 Create `TransactionsTable` — shadcn `Table`; columns differ by type (bank vs card); `AmountDisplay` in amount cell; installment badge for card; sorted newest first
- [ ] 19.5 Create `PaginationBar` — previous/next + page info ("51–100 of 312"); wired to offset param
- [ ] 19.6 Create `/transactions` page — tab bar Bank / Card; `TransactionFilters`; `TransactionsTable` with `PaginationBar`; `LoadingSkeleton` (8 rows); `EmptyState` when no results
- [ ] 19.7 Text search: client-side filter on `description_raw` within the current page (no backend change required for Cycle 1)
- [ ] 19.8 Filter state in URL: `?tab=bank&instrument_id=…&date_from=…&date_to=…&page=2`

**Acceptance:** Transactions load with pagination (50/page). Instrument + date filters work. Tab switches between bank and card. Empty state shown when no results. URL reflects filter state (shareable/bookmarkable).

---

## Phase 20 — Statements Page

- [ ] 20.1 Create `useStatements` hook — `GET /card-statements?instrument_id=…`
- [ ] 20.2 Create `StatementCard` — period range, due date, total (`AmountDisplay`), status badge
- [ ] 20.3 Create `StatementDetailDrawer` — shadcn `Sheet`; statement metadata; "View transactions" link → `/transactions?tab=card&instrument_id=…&date_from=…&date_to=…`
- [ ] 20.4 Create `/statements` page — `InstrumentPicker` (credit_card type only); list of `StatementCard`; `LoadingSkeleton`; `EmptyState`
- [ ] 20.5 Sort statements newest-first by `statement_end`

**Acceptance:** Statements list filtered by card instrument. "View transactions" link opens transactions page pre-filtered to that statement's date range.

---

## Phase 21 — Dashboard

- [ ] 21.1 Create `useSpendingSummary` hook — `GET /spending-summary?date_from=…&date_to=…`; default to current calendar month
- [ ] 21.2 Create `SummaryCards` — 3 stat cards: Total Expenses (current month), Total Transactions, Last Import date; `LoadingSkeleton` per card
- [ ] 21.3 Create `SpendingChart` — Recharts `BarChart` (horizontal) or `PieChart`; categories on y-axis; amounts on x-axis; "Uncategorized" bucket at bottom; empty state if no data
- [ ] 21.4 Create `RecentImportsWidget` — last 5 batches (`GET /imports?limit=5`); compact list; "View all" link
- [ ] 21.5 Create QuickActions section — two `Card` CTAs: "Import a statement" → `/import/new`, "View transactions" → `/transactions`
- [ ] 21.6 Create `/` (Dashboard) page — month picker in topbar; `SummaryCards` + `SpendingChart` + `RecentImportsWidget` + `QuickActions`
- [ ] 21.7 Full-page `EmptyState` (onboarding) when no instruments exist — step list: Add instrument → Import file → View data

**Acceptance:** Dashboard loads with current month spending summary. Chart renders. Recent imports show. Quick actions navigate correctly. Empty/onboarding state shown on first run.

---

## Phase 22 — UI Polish & Accessibility

- [ ] 22.1 Add `LoadingSkeleton` to every page and component that fetches data (audit all pages)
- [ ] 22.2 Add `EmptyState` to every list view (audit all pages)
- [ ] 22.3 Verify all error cases show toast with informative message (network error, 422, 404, 500)
- [ ] 22.4 Responsive audit: test all pages at 375px (mobile), 768px (tablet), 1280px (desktop)
- [ ] 22.5 Mobile nav: hamburger opens sidebar as a `Sheet` overlay
- [ ] 22.6 Accessibility audit: keyboard navigation through all forms and tables; ARIA labels on icon-only buttons; focus ring visible
- [ ] 22.7 Color contrast: verify all text passes WCAG AA (4.5:1 for normal, 3:1 for large)
- [ ] 22.8 Consistent spacing pass: verify `p-6` page padding, `gap-4` card grids, `space-y-6` sections across all pages

**Acceptance:** All pages usable on mobile. No layout shift on load. Keyboard-navigable. All errors surfaced via toast. Skeletons match content shape.

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
