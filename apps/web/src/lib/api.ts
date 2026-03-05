import type { components } from "@/lib/api-types"

// ---------------------------------------------------------------------------
// Exported types (shorthand aliases)
// ---------------------------------------------------------------------------

export type InstrumentOut = components["schemas"]["InstrumentOut"]
export type InstrumentCreate = components["schemas"]["InstrumentCreate"]
export type InstrumentUpdate = components["schemas"]["InstrumentUpdate"]
export type InstrumentSource = components["schemas"]["InstrumentSource"]
export type InstrumentType = components["schemas"]["InstrumentType"]

export type ImportBatchOut = components["schemas"]["ImportBatchOut"]
export type ImportStatus = components["schemas"]["ImportStatus"]

export type BankTransactionOut = components["schemas"]["BankTransactionOut"]
export type CardTransactionOut = components["schemas"]["CardTransactionOut"]
export type CardStatementOut = components["schemas"]["CardStatementOut"]
export type StatementStatus = components["schemas"]["StatementStatus"]

export type SpendingSummaryOut = components["schemas"]["SpendingSummaryOut"]
export type CategoryOut = components["schemas"]["CategoryOut"]

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = await res.json()
      message = body?.detail ?? JSON.stringify(body) ?? message
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, message)
  }
  return res
}

// ---------------------------------------------------------------------------
// Instruments
// ---------------------------------------------------------------------------

export async function getInstruments(): Promise<InstrumentOut[]> {
  const res = await apiFetch("/instruments")
  return res.json()
}

export async function createInstrument(
  data: InstrumentCreate,
): Promise<InstrumentOut> {
  const res = await apiFetch("/instruments", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function updateInstrument(
  id: string,
  data: InstrumentUpdate,
): Promise<InstrumentOut> {
  const res = await apiFetch(`/instruments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return res.json()
}

// ---------------------------------------------------------------------------
// Import batches
// ---------------------------------------------------------------------------

export async function getImports(params: {
  instrument_id?: string
  limit?: number
  offset?: number
}): Promise<ImportBatchOut[]> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/imports?${qs}`)
  return res.json()
}

export async function getImportBatch(id: string): Promise<ImportBatchOut> {
  const res = await apiFetch(`/imports/${id}`)
  return res.json()
}

export async function uploadFile(
  instrumentId: string,
  file: File,
): Promise<ImportBatchOut> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(
    `${BASE_URL}/imports/upload?instrument_id=${instrumentId}`,
    { method: "POST", body: form },
  )
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = await res.json()
      message = body?.detail ?? message
    } catch {
      // ignore
    }
    throw new ApiError(res.status, message)
  }
  return res.json()
}

// ---------------------------------------------------------------------------
// Bank transactions
// ---------------------------------------------------------------------------

export async function getBankTransactions(params: {
  instrument_id?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}): Promise<BankTransactionOut[]> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.date_from) qs.set("date_from", params.date_from)
  if (params.date_to) qs.set("date_to", params.date_to)
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/bank-transactions?${qs}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Card transactions
// ---------------------------------------------------------------------------

export async function getCardTransactions(params: {
  instrument_id?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}): Promise<CardTransactionOut[]> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.date_from) qs.set("date_from", params.date_from)
  if (params.date_to) qs.set("date_to", params.date_to)
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/card-transactions?${qs}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Card statements
// ---------------------------------------------------------------------------

export async function getCardStatements(params: {
  instrument_id?: string
}): Promise<CardStatementOut[]> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  const res = await apiFetch(`/card-statements?${qs}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Spending summary
// ---------------------------------------------------------------------------

export async function getSpendingSummary(params: {
  date_from: string
  date_to: string
  instrument_id?: string
}): Promise<SpendingSummaryOut> {
  const qs = new URLSearchParams({
    date_from: params.date_from,
    date_to: params.date_to,
  })
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  const res = await apiFetch(`/spending-summary?${qs}`)
  return res.json()
}
