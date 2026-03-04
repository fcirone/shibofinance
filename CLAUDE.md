# Finance OS — Local Personal Finance System

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