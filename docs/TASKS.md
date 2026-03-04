# Finance OS — Execution Plan

Progress legend: `[ ]` pending · `[x]` done

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

- [ ] 4.1 Configure `apps/api/alembic.ini`
- [ ] 4.2 Configure `apps/api/alembic/env.py` (async-compatible, reads `DATABASE_URL` from env)
- [ ] 4.3 Generate initial migration from models
- [ ] 4.4 Confirm `make migrate` applies migrations cleanly against running Postgres

---

## Phase 5 — Core Packages

- [ ] 5.1 `packages/core/money.py` — integer minor-unit conversion helpers
- [ ] 5.2 `packages/core/timezones.py` — timezone constants and UTC conversion
- [ ] 5.3 `packages/core/normalizers.py` — description normalization (lowercase, remove accents, collapse whitespace, remove duplicate punctuation)
- [ ] 5.4 `packages/core/fingerprint.py` — SHA256 fingerprint generation from `(instrument_id, posted_date, currency, amount_minor, description_norm)`

---

## Phase 6 — Importer Framework

- [ ] 6.1 Define `packages/importers/base.py` — `BaseImporter` interface (`SOURCE_NAME`, `detect()`, `parse()`) and `ImportResult` dataclass
- [ ] 6.2 Implement `packages/importers/registry.py` — auto-detects importer from file bytes + filename
- [ ] 6.3 Implement `apps/api/services/fingerprint_service.py` — wraps core fingerprint logic
- [ ] 6.4 Implement `apps/api/services/dedupe_service.py` — upsert logic using `fingerprint_hash` / `source_tx_id`
- [ ] 6.5 Implement `apps/api/services/import_service.py` — orchestrates full import pipeline (detect → parse → normalize → fingerprint → upsert → statement → match)

---

## Phase 7 — Santander Brazil Importer

- [ ] 7.1 `packages/importers/santander_br/detector.py` — detect Santander BR files
- [ ] 7.2 `packages/importers/santander_br/bank_parser_csv.py` — parse bank statement CSV
- [ ] 7.3 `packages/importers/santander_br/card_parser_pdf.py` — parse credit card PDF
- [ ] 7.4 Add sample files to `data/samples/santander_br/`
- [ ] 7.5 Manually test import of both file types

---

## Phase 8 — XP Brazil Importer

- [ ] 8.1 `packages/importers/xp_br/detector.py`
- [ ] 8.2 `packages/importers/xp_br/bank_parser_csv.py`
- [ ] 8.3 `packages/importers/xp_br/card_parser_csv.py`
- [ ] 8.4 Add sample files to `data/samples/xp_br/`
- [ ] 8.5 Manually test import of both file types

---

## Phase 9 — BBVA Uruguay Importer

- [ ] 9.1 `packages/importers/bbva_uy/detector.py`
- [ ] 9.2 `packages/importers/bbva_uy/bank_parser_csv.py`
- [ ] 9.3 `packages/importers/bbva_uy/card_parser_pdf.py`
- [ ] 9.4 Add sample files to `data/samples/bbva_uy/`
- [ ] 9.5 Manually test import of both file types

---

## Phase 10 — Statement Payment Matching

- [ ] 10.1 Implement `apps/api/services/statement_matcher.py`
  - [ ] 10.1.1 Detect payment patterns: `PAGAMENTO FATURA`, `PAGTO CARTAO`, `CARD PAYMENT`
  - [ ] 10.1.2 Match by amount (exact or partial) and date proximity to statement due date
  - [ ] 10.1.3 Insert record into `statement_payment_links`
  - [ ] 10.1.4 Auto-categorize matched bank transaction as `transfer`

---

## Phase 11 — API Endpoints

- [ ] 11.1 `app/main.py` — FastAPI app setup, router registration
- [ ] 11.2 `app/schemas.py` — Pydantic v2 request/response schemas
- [ ] 11.3 `app/routers/health.py` — `GET /health`
- [ ] 11.4 `app/routers/instruments.py` — `POST /instruments`, `GET /instruments`
- [ ] 11.5 `app/routers/imports.py` — `POST /imports/upload`
- [ ] 11.6 `app/routers/bank_transactions.py` — `GET /bank-transactions`
- [ ] 11.7 `app/routers/card_transactions.py` — `GET /card-transactions`
- [ ] 11.8 `app/routers/statements.py` — `GET /card-statements`
- [ ] 11.9 `app/routers/categories.py` — `GET /categories`, `POST /categorize`
- [ ] 11.10 `app/routers/spending_summary.py` — `GET /spending-summary` (card txs + bank txs excluding transfers)

---

## Phase 12 — CLI Tool

- [ ] 12.1 Implement `tools/import_cli.py`
  - [ ] 12.1.1 `import` command (`--file`, `--instrument`, `--source auto`)
  - [ ] 12.1.2 `list-transactions` command (`--instrument`)

---

## Phase 13 — Tests

- [ ] 13.1 `tests/test_health.py` — health endpoint returns 200
- [ ] 13.2 `tests/test_import_idempotency.py` — reimporting same file produces no new rows
- [ ] 13.3 Fingerprint consistency test — same input always produces same hash
- [ ] 13.4 Basic query test — imported transactions appear in GET endpoints
- [ ] 13.5 Confirm `make test` passes with all tests green

---

## Acceptance Checklist

- [ ] `docker compose up` starts the full system
- [ ] API is reachable at `http://localhost:8000`
- [ ] Can create instruments via `POST /instruments`
- [ ] Can upload a CSV/PDF via `POST /imports/upload`
- [ ] Transactions appear in `GET /bank-transactions` or `GET /card-transactions`
- [ ] Re-importing the same file produces zero new rows (idempotency)
- [ ] `GET /spending-summary` returns correct totals
