# Finance OS

Local-first personal finance system. Imports bank and credit card statements from Brazilian and Uruguayan banks into a unified ledger with categorization.

## Supported banks

| Bank | Country | Bank statement | Credit card |
|---|---|---|---|
| Santander | Brazil | PDF | PDF |
| XP | Brazil | CSV | CSV |
| BBVA | Uruguay | CSV | PDF |

## Requirements

- Docker + Docker Compose
- Python 3.12+ with `httpx` installed (for the CLI only)

## Setup

```bash
cp .env.example .env
make up
make migrate
```

API will be available at `http://localhost:8000`.

---

## Make commands

| Command | Description |
|---|---|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Tail service logs |
| `make migrate` | Run Alembic migrations |
| `make test` | Run test suite |
| `make api-shell` | Open shell inside api container |

---

## CLI

All CLI commands talk to `http://localhost:8000` by default.
Override with `--api-base` or the `API_BASE` environment variable.

```bash
python tools/import_cli.py --help
python tools/import_cli.py <command> --help
```

### 1. Create an instrument

You must create an instrument before importing files. The command returns the UUID you'll use in subsequent commands.

```bash
python tools/import_cli.py create-instrument \
  --name "Santander Conta Corrente" \
  --type bank_account \
  --source santander_br \
  --currency BRL \
  --source-instrument-id santander-conta
```

#### Parameter reference

| Parameter | Values | Notes |
|---|---|---|
| `--type` | `bank_account` · `credit_card` | |
| `--source` | `santander_br` · `xp_br` · `bbva_uy` | |
| `--currency` | `BRL` · `USD` · `UYU` | |
| `--source-instrument-id` | any string | Stable user-defined key — must be unique per source |

#### Examples for each instrument

```bash
# Santander BR — conta corrente
python tools/import_cli.py create-instrument \
  --name "Santander Conta" \
  --type bank_account \
  --source santander_br \
  --currency BRL \
  --source-instrument-id santander-conta

# Santander BR — cartão de crédito (PDF protegido por senha = CPF sem pontuação)
python3 tools/import_cli.py create-instrument \
  --name "Santander Cartão" \
  --type credit_card \
  --source santander_br \
  --currency BRL \
  --source-instrument-id santander-cartao \
  --metadata '{"pdf_password": "12345678900"}'

# XP BR — conta corrente
python tools/import_cli.py create-instrument \
  --name "XP Conta" \
  --type bank_account \
  --source xp_br \
  --currency BRL \
  --source-instrument-id xp-conta

# XP BR — cartão de crédito
python tools/import_cli.py create-instrument \
  --name "XP Cartão" \
  --type credit_card \
  --source xp_br \
  --currency BRL \
  --source-instrument-id xp-cartao

# BBVA UY — cuenta corriente
python tools/import_cli.py create-instrument \
  --name "BBVA Cuenta" \
  --type bank_account \
  --source bbva_uy \
  --currency UYU \
  --source-instrument-id bbva-cuenta

# BBVA UY — tarjeta de crédito
python tools/import_cli.py create-instrument \
  --name "BBVA Tarjeta" \
  --type credit_card \
  --source bbva_uy \
  --currency UYU \
  --source-instrument-id bbva-tarjeta
```

### 2. List instruments

```bash
python tools/import_cli.py list-instruments
```

### 3. Import a file

```bash
python tools/import_cli.py import \
  --file path/to/statement.pdf \
  --instrument <uuid>
```

The importer is auto-detected from the file contents and name. Output shows inserted, duplicate, and error counts.

### 4. List transactions

```bash
# All transactions
python tools/import_cli.py list-transactions

# Filter by instrument
python tools/import_cli.py list-transactions --instrument <uuid>
```

---

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/instruments` | Create instrument |
| GET | `/instruments` | List instruments |
| POST | `/imports/upload` | Upload statement file |
| GET | `/bank-transactions` | List bank transactions |
| GET | `/card-transactions` | List card transactions |
| GET | `/card-statements` | List card statements |
| POST | `/categorize` | Categorize a transaction |
| GET | `/categories` | List categories |
| GET | `/spending-summary` | Spending summary |

Interactive docs: `http://localhost:8000/docs`

---

## Design principles

- All monetary values stored as integer minor units (e.g. 100.50 BRL → 10050)
- All timestamps stored in UTC
- Imports are idempotent — re-importing the same file produces no duplicate rows
- Original raw data always preserved in `raw_payload` (JSONB)
- Credit card purchases are expenses; credit card bill payments are transfers
