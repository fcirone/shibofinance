# Finance OS — Frontend UI Specification (Cycle 1)

> Spec version: 1.0 · Cycle: MVP UI
> Reference: [CLAUDE.md](../CLAUDE.md) · [TASKS.md](TASKS.md)

---

## 1. Product Vision

Finance OS is a local-first personal finance tool for people who manage money across multiple banks and countries. The UI must feel like a **premium SaaS dashboard** — not a side project. Clear hierarchy, generous whitespace, smooth interactions, and zero ambiguity.

**Productization principle:** copywriting and component design should be neutral and reusable — not tied to a specific user's name, bank, or country. Anyone onboarding should immediately understand the workflow.

---

## 2. Information Architecture

```
/                           Dashboard (overview + quick actions)
/instruments                Instruments list + create/edit
/import/new                 Upload a statement file
/imports                    Import history (all batches)
/imports/[id]               Batch detail (redirect to /imports with drawer open)
/transactions               All transactions (bank + card, unified table)
/statements                 Credit card statements list + detail drawer
```

### Navigation (Sidebar)

| Icon | Label | Route |
|------|-------|-------|
| LayoutDashboard | Dashboard | / |
| CreditCard | Instruments | /instruments |
| Upload | Import | /import/new |
| History | Import History | /imports |
| List | Transactions | /transactions |
| FileText | Statements | /statements |

Active item highlighted. Sidebar collapses to icon-only on `lg` breakpoint and below (hamburger on mobile).

---

## 3. Key User Journeys

### Journey 1 — First Run (Onboarding)
1. User arrives at `/` — dashboard empty state with "Get started" prompt.
2. User clicks "Add Instrument" → `/instruments` → CreateInstrumentDialog opens.
3. After creating instrument, user is nudged: "Now import a statement file."
4. User clicks "Import file" → `/import/new`.
5. User selects instrument, drops PDF/CSV → result shows inserted count.
6. User navigates to `/transactions` → sees their data.

### Journey 2 — Regular Import
1. User goes to `/import/new`.
2. Selects instrument from picker (or inline creates one).
3. Drops file → upload + processing (spinner) → result batch card.
4. "View transactions" CTA in result links to `/transactions?instrument_id=…`.

### Journey 3 — Browse Transactions
1. User opens `/transactions`.
2. Selects instrument filter → table updates.
3. Sets date range → table updates.
4. Switches tab Bank ↔ Card.
5. Searches description text (debounced).
6. Pages through results (50 per page).

### Journey 4 — Review Card Statement
1. User opens `/statements`.
2. Sees list of statements by card instrument.
3. Clicks a statement → drawer opens with statement details + link to filtered `/transactions`.

### Journey 5 — Dashboard Overview
1. User opens `/` → sees spending summary for current month.
2. Chart shows total expenses (categorized + uncategorized).
3. Recent imports widget shows last 3 batches.
4. Quick action cards: Import, View Transactions.

---

## 4. Page Specifications

### 4.1 Dashboard `/`

**Components:**
- TopBar with page title + date range picker (default: current month)
- `SummaryCards` row: Total Expenses (current month) · Total Transactions · Last Import
- `SpendingChart`: horizontal bar chart or donut; total breakdown by category + "Uncategorized" bucket; powered by `GET /spending-summary`
- `RecentImportsWidget`: last 5 batches from `GET /imports?limit=5`
- `QuickActions`: two CTA cards — "Import a statement" and "Browse transactions"

**Empty state:** Full-page welcome panel with onboarding steps checklist (Add instrument → Import file → View data).

**API calls:**
- `GET /spending-summary?date_from=…&date_to=…`
- `GET /imports?limit=5&offset=0`

---

### 4.2 Instruments `/instruments`

**Components:**
- Page header with "Add Instrument" button
- `InstrumentGrid`: responsive grid of `InstrumentCard` components
- `InstrumentCard`: name, type badge (Bank / Credit Card), source badge (santander_br etc.), currency, created date
- `CreateInstrumentDialog`: modal form
- `EditInstrumentDialog`: modal form (name + metadata JSON editor)

**CreateInstrumentDialog fields:**
| Field | Input | Validation |
|-------|-------|------------|
| Name | text | required, min 2 |
| Type | select: bank_account \| credit_card | required |
| Source | select: santander_br \| xp_br \| bbva_uy | required |
| Currency | select: BRL \| USD \| UYU | required |
| Source Instrument ID | text | optional, unique hint |
| Metadata (JSON) | textarea | optional, valid JSON |

**Empty state:** Illustration + "No instruments yet. Add your first bank account or credit card."

**API calls:**
- `GET /instruments`
- `POST /instruments`
- `PATCH /instruments/{id}`

---

### 4.3 Import New `/import/new`

**Components:**
- `InstrumentPicker`: searchable select from instruments list
- `UploadDropzone`: drag-and-drop zone
  - Accepted types: `.pdf`, `.csv`, `.ofx`
  - Max size: 20 MB
  - Shows file name + size after selection
  - Validates before submitting
- Submit button: "Import File" (disabled until instrument + file selected)
- `ImportResultCard`: shown after success — filename, inserted, duplicates, errors, status badge
- Error toast on failure with backend message

**State machine:**
```
idle → file_selected → uploading → success | error
```

**API calls:**
- `GET /instruments` (for picker)
- `POST /imports/upload` (multipart)

---

### 4.4 Import History `/imports`

**Components:**
- Filter bar: `InstrumentPicker` (all instruments, optional filter)
- `ImportBatchList`: scrollable list of `ImportBatchCard`
- `ImportBatchCard`: filename, instrument name, status badge, inserted/dup/error counts, date
- `BatchDetailDrawer`: slide-out from right
  - Batch metadata (id, sha256 hash truncated, processed_at)
  - Counts summary
  - "View transactions" link → `/transactions?instrument_id=…`

**Status badge colors:**
- `processed` → green
- `failed` → red
- `created` → yellow (in-progress)

**Empty state:** "No imports yet. Upload your first statement file."

**Pagination:** infinite scroll or "Load more" button (50 per page).

**API calls:**
- `GET /imports?instrument_id=…&limit=50&offset=…`
- `GET /imports/{id}` (for drawer)

---

### 4.5 Transactions `/transactions`

**Components:**
- Tab bar: **Bank Transactions** | **Card Transactions**
- Filter bar (collapsible on mobile):
  - `InstrumentPicker`
  - Date range picker (from / to)
  - Text search input (debounced 400ms, searches description_raw client-side on loaded page)
- `TransactionsTable`: sortable by date (default: newest first)
- `AmountCell`: format minor units → `R$ 1.234,56` / `$ 1,234.56` / `$ U 1.234,56` per currency; negative = red, positive = green
- `PaginationBar`: page controls, showing "51–100 of 312"
- Row click: no action in Cycle 1 (Cycle 2: categorize drawer)

**Table columns — Bank Transactions:**
| Date | Description | Instrument | Amount | Currency |

**Table columns — Card Transactions:**
| Date | Description | Instrument | Amount | Currency | Installment |

**Installment cell:** shows `2/12` badge if installment_number/installments_total present.

**Page size:** 50 rows. Server-side via `limit=50&offset=N`.

**Empty state:** "No transactions found. Try adjusting your filters."

**API calls:**
- `GET /bank-transactions?instrument_id=…&date_from=…&date_to=…&limit=50&offset=…`
- `GET /card-transactions?instrument_id=…&date_from=…&date_to=…&limit=50&offset=…`
- `GET /instruments` (for picker)

---

### 4.6 Statements `/statements`

**Components:**
- Filter: `InstrumentPicker` (credit card instruments only)
- `StatementList`: list of `StatementCard`
- `StatementCard`: period range, due date, total amount, status badge
- `StatementDetailDrawer`:
  - Statement metadata
  - Total formatted
  - Status + due date
  - "View transactions" link → `/transactions?instrument_id=…&date_from=…&date_to=…`

**Status badge colors:**
- `open` → blue
- `paid` → green
- `partial` → yellow
- `closed` → gray

**Empty state:** "No credit card statements imported yet."

**API calls:**
- `GET /card-statements?instrument_id=…`
- `GET /instruments` (for picker, filtered to credit_card type)

---

## 5. Component Library

### Reusable components (`apps/web/src/components/`)

| Component | Description |
|-----------|-------------|
| `AppShell` | Sidebar + topbar layout wrapper |
| `InstrumentPicker` | Searchable select for instruments |
| `UploadDropzone` | Drag-and-drop file input with validation |
| `TransactionsTable` | Generic table with pagination |
| `ImportBatchCard` | Single import batch summary card |
| `BatchDetailDrawer` | Slide-out batch detail panel |
| `StatementCard` | Credit card statement summary |
| `StatementDetailDrawer` | Slide-out statement detail |
| `EmptyState` | Reusable empty state (icon + title + description + CTA) |
| `LoadingSkeleton` | Skeleton placeholder matching component shape |
| `AmountDisplay` | Format minor-unit integer → localized currency string |
| `StatusBadge` | Colored badge for import/statement status |
| `SourceBadge` | Colored badge for instrument source (santander_br, etc.) |
| `DateRangePicker` | Two-date calendar picker |
| `PageHeader` | Page title + optional action button |

---

## 6. Design System

### Typography
- Font: `Inter` (Google Fonts or system)
- Headings: `font-semibold`, scale: `text-2xl` (page) → `text-lg` (section) → `text-base` (card)
- Body: `text-sm text-muted-foreground`
- Monospace: amounts, hashes, IDs

### Color Palette (shadcn/ui tokens)
- Background: `background` / `card`
- Primary: used for CTAs and active nav
- Destructive: errors, failed status
- Muted: secondary text, borders
- Custom semantic: green for income/positive, red for debit/negative

### Spacing
- Page padding: `p-6` (desktop), `p-4` (mobile)
- Card gap: `gap-4`
- Section spacing: `space-y-6`

### Amounts Display
```
BRL: R$ 1.234,56   (Brazilian format)
USD: $ 1,234.56    (US format)
UYU: $ U 1.234,56  (Uruguayan format)
```
Negative amounts displayed in red. Positive in default foreground (bank credits) or green (card payments).

---

## 7. Loading & Empty States

### Loading
Every data-fetching component must show a `LoadingSkeleton` while `isLoading` (TanStack Query). Skeletons must match the approximate shape of the real content (not just a generic spinner).

| Component | Skeleton |
|-----------|----------|
| InstrumentCard | Rounded rect 200×80px |
| ImportBatchCard | 2-line text block |
| TransactionsTable | 8 rows × 5 columns of text lines |
| StatementCard | 3-line card |
| SummaryCards | 3 number cards |

### Empty States
Every list component must have an `EmptyState` with:
- Icon (Lucide)
- Title (what is missing)
- Description (why and what to do)
- Optional CTA button

### Errors
- Query errors → toast notification via shadcn/ui `Sonner` or `useToast`
- Form errors → inline field-level messages (React Hook Form + Zod)
- Upload errors → error card replacing the dropzone result area
- Network down → toast "Could not connect to API. Make sure the backend is running."

---

## 8. Responsiveness

| Breakpoint | Layout |
|------------|--------|
| `< 768px` | Mobile: hamburger nav, stacked filters, horizontal scroll on table |
| `768–1024px` | Tablet: collapsible sidebar icons only |
| `> 1024px` | Desktop: full sidebar, side-by-side panels |

Drawers are full-screen on mobile.

---

## 9. Accessibility (A11y)

- All interactive elements keyboard-navigable
- ARIA labels on icon-only buttons
- Color is never the only signal (status badges have text)
- Focus ring visible on all focusable elements (`outline-ring/50`)
- Table has proper `<thead>`, `scope="col"`, `role="grid"` attributes
- Skip-to-content link in AppShell

---

## 10. Future Roadmap Notes (Cycle 2+)

These are intentionally **out of scope** for Cycle 1 but the architecture should not make them hard:

| Feature | Notes |
|---------|-------|
| Transaction categorization | Click a row → assign category. Backend already has `POST /categorize`. |
| Categorization rules engine | Regex/keyword rules → auto-categorize on import. Backend stub exists. |
| Budget goals per category | New backend feature needed. |
| Multi-currency normalization | Dashboard total needs a reference currency + exchange rates. |
| Auth / multi-user | Wrap API in auth middleware. UI gets login page. |
| Cloud deployment | Add Nginx reverse proxy, TLS, env-based secrets. |
| Mobile app | React Native sharing components + API client. |
| CSV export | `GET /bank-transactions?format=csv` backend addition. |
| Notifications | Webhook or local notification when import completes. |

---

## 11. API Client Contract

The frontend generates TypeScript types from the FastAPI OpenAPI schema:

```bash
# Regenerate after any backend schema change
npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api-types.ts
```

The typed API client (`src/lib/api.ts`) wraps `fetch` calls with:
- Base URL from `NEXT_PUBLIC_API_BASE_URL` env var
- All request/response types inferred from generated types
- Error normalization: any non-2xx → `ApiError` with `message` and `status`

No third-party HTTP library required (raw `fetch` + generated types is sufficient for this scale).
