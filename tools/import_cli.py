#!/usr/bin/env python3
"""Finance OS CLI — import files and query transactions via the API."""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required: pip install httpx", file=sys.stderr)
    sys.exit(1)

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=60)


def _print_table(rows: list[dict], columns: list[str]) -> None:
    if not rows:
        print("(no results)")
        return
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    sep = "  ".join("-" * widths[col] for col in columns)
    print(header)
    print(sep)
    for row in rows:
        print("  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_import(args: argparse.Namespace) -> int:
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1

    with _client() as client:
        with open(file_path, "rb") as fh:
            resp = client.post(
                "/imports/upload",
                params={"instrument_id": args.instrument},
                files={"file": (file_path.name, fh)},
            )

    if resp.status_code not in (200, 201):
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    batch = resp.json()
    print(f"Import complete — batch {batch['id']}")
    print(f"  inserted:   {batch['inserted_count']}")
    print(f"  duplicates: {batch['duplicate_count']}")
    print(f"  errors:     {batch['error_count']}")
    print(f"  status:     {batch['status']}")
    return 0


def cmd_create_instrument(args: argparse.Namespace) -> int:
    payload: dict = {
        "name": args.name,
        "type": args.type,
        "source": args.source,
        "currency": args.currency,
        "source_instrument_id": args.source_instrument_id,
    }
    if args.metadata:
        try:
            payload["metadata_"] = json.loads(args.metadata)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in --metadata: {exc}", file=sys.stderr)
            return 1

    with _client() as client:
        resp = client.post("/instruments", json=payload)

    if resp.status_code not in (200, 201):
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    inst = resp.json()
    print(f"Instrument created — {inst['id']}")
    print(f"  name:   {inst['name']}")
    print(f"  type:   {inst['type']}")
    print(f"  source: {inst['source']}")
    print(f"  currency: {inst['currency']}")
    return 0


def cmd_update_instrument(args: argparse.Namespace) -> int:
    payload: dict = {}
    if args.name:
        payload["name"] = args.name
    if args.metadata:
        try:
            payload["metadata_"] = json.loads(args.metadata)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in --metadata: {exc}", file=sys.stderr)
            return 1
    if not payload:
        print("Nothing to update — provide --name and/or --metadata", file=sys.stderr)
        return 1

    with _client() as client:
        resp = client.patch(f"/instruments/{args.instrument}", json=payload)

    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    inst = resp.json()
    print(f"Instrument updated — {inst['id']}")
    print(f"  name:     {inst['name']}")
    print(f"  metadata: {inst['metadata_']}")
    return 0


def cmd_list_instruments(args: argparse.Namespace) -> int:
    with _client() as client:
        resp = client.get("/instruments")

    if resp.status_code != 200:
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        return 1

    instruments = resp.json()
    _print_table(instruments, ["id", "name", "type", "source", "currency", "source_instrument_id"])
    return 0


def cmd_list_transactions(args: argparse.Namespace) -> int:
    params: dict = {}
    if args.instrument:
        params["instrument_id"] = args.instrument

    with _client() as client:
        bank_resp = client.get("/bank-transactions", params=params)
        card_resp = client.get("/card-transactions", params={
            k.replace("instrument_id", "instrument_id"): v for k, v in params.items()
        })

    if bank_resp.status_code != 200:
        print(f"Error fetching bank transactions: {bank_resp.text}", file=sys.stderr)
        return 1
    if card_resp.status_code != 200:
        print(f"Error fetching card transactions: {card_resp.text}", file=sys.stderr)
        return 1

    bank_txs = bank_resp.json()
    card_txs = card_resp.json()

    if bank_txs:
        print(f"\n=== Bank Transactions ({len(bank_txs)}) ===")
        _print_table(bank_txs, ["id", "posted_date", "description_raw", "amount_minor", "currency"])

    if card_txs:
        print(f"\n=== Card Transactions ({len(card_txs)}) ===")
        _print_table(card_txs, ["id", "posted_date", "description_raw", "amount_minor", "currency"])

    if not bank_txs and not card_txs:
        print("No transactions found.")

    return 0


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="import_cli.py",
        description="Finance OS CLI",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help=f"API base URL (default: {API_BASE})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create-instrument
    p_create = sub.add_parser("create-instrument", help="Create a new instrument (bank account or credit card)")
    p_create.add_argument("--name", required=True, help="Human-readable name")
    p_create.add_argument(
        "--type", required=True, choices=["bank_account", "credit_card"],
        help="bank_account or credit_card",
    )
    p_create.add_argument(
        "--source", required=True, choices=["santander_br", "xp_br", "bbva_uy"],
        help="Bank source identifier",
    )
    p_create.add_argument(
        "--currency", required=True, choices=["BRL", "USD", "UYU"],
        help="Account currency",
    )
    p_create.add_argument(
        "--source-instrument-id", dest="source_instrument_id", required=True,
        help="Stable user-defined identifier (e.g. 'santander-conta-corrente')",
    )
    p_create.add_argument(
        "--metadata", default=None,
        help='JSON metadata, e.g. \'{"pdf_password": "12345678900"}\'',
    )

    # update-instrument
    p_update = sub.add_parser("update-instrument", help="Update name or metadata of an existing instrument")
    p_update.add_argument("--instrument", required=True, help="Instrument UUID")
    p_update.add_argument("--name", default=None, help="New name")
    p_update.add_argument("--metadata", default=None, help='JSON metadata, e.g. \'{"pdf_password": "12345678900"}\'')

    # list-instruments
    sub.add_parser("list-instruments", help="List all instruments")

    # import
    p_import = sub.add_parser("import", help="Import a file for an instrument")
    p_import.add_argument("--file", required=True, help="Path to the file to import")
    p_import.add_argument("--instrument", required=True, help="Instrument UUID")
    p_import.add_argument(
        "--source",
        default="auto",
        help="Importer source name or 'auto' (default: auto)",
    )

    # list-transactions
    p_list = sub.add_parser("list-transactions", help="List transactions for an instrument")
    p_list.add_argument("--instrument", required=False, default=None, help="Instrument UUID (optional filter)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.api_base:
        global API_BASE
        API_BASE = args.api_base

    dispatch = {
        "create-instrument": cmd_create_instrument,
        "update-instrument": cmd_update_instrument,
        "list-instruments": cmd_list_instruments,
        "import": cmd_import,
        "list-transactions": cmd_list_transactions,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
