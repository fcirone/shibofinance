# Finance OS

Local-first personal finance system. Imports bank and credit card statements from Brazilian and Uruguayan banks into a unified ledger with categorization.

## Supported banks

| Bank | Country | Bank statement | Credit card |
|---|---|---|---|
| Santander | Brazil | CSV | PDF |
| XP | Brazil | CSV | CSV |
| BBVA | Uruguay | CSV | PDF |

## Requirements

- Docker + Docker Compose

## Setup

```bash
cp .env.example .env
make up
make migrate
```

API will be available at `http://localhost:8000`.

## Commands

| Command | Description |
|---|---|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Tail service logs |
| `make migrate` | Run Alembic migrations |
| `make test` | Run test suite |
| `make api-shell` | Open shell inside api container |

## Import via CLI

```bash
# Import a file
python tools/import_cli.py import \
  --file path/to/statement.csv \
  --instrument <instrument_id> \
  --source auto

# List transactions
python tools/import_cli.py list-transactions \
  --instrument <instrument_id>
```

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

## Design principles

- All monetary values stored as integer minor units (e.g. 100.50 BRL → 10050)
- All timestamps stored in UTC
- Imports are idempotent — re-importing the same file produces no duplicate rows
- Original raw data always preserved in `raw_payload` (JSONB)
- Credit card purchases are expenses; credit card bill payments are transfers
