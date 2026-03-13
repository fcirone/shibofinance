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
export type CategoryCreate = components["schemas"]["CategoryCreate"]
export type CategoryUpdate = components["schemas"]["CategoryUpdate"]
export type CategoryKind = components["schemas"]["CategoryKind"]
export type CategorizationOut = components["schemas"]["CategorizationOut"]
export type CategorizeRequest = components["schemas"]["CategorizeRequest"]
export type BulkCategorizeRequest = components["schemas"]["BulkCategorizeRequest"]
export type BulkCategorizeResult = components["schemas"]["BulkCategorizeResult"]
export type TargetType = components["schemas"]["TargetType"]

export type CategoryRuleOut = components["schemas"]["CategoryRuleOut"]
export type CategoryRuleCreate = components["schemas"]["CategoryRuleCreate"]
export type CategoryRuleUpdate = components["schemas"]["CategoryRuleUpdate"]
export type MatchField = components["schemas"]["MatchField"]
export type MatchOperator = components["schemas"]["MatchOperator"]
export type RuleTargetType = components["schemas"]["RuleTargetType"]
export type DryRunResult = components["schemas"]["DryRunResult"]
export type ApplyRulesResult = components["schemas"]["ApplyRulesResult"]

// ---------------------------------------------------------------------------
// Paged result wrapper
// ---------------------------------------------------------------------------

export interface PagedResult<T> {
  data: T[]
  total: number
}

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
      const detail = body?.detail
      if (typeof detail === "string") {
        message = detail
      } else if (Array.isArray(detail)) {
        // FastAPI validation errors: [{loc, msg, type}, ...]
        message = detail
          .map((d: { msg?: string; loc?: string[] }) =>
            [d.loc?.slice(-1)[0], d.msg].filter(Boolean).join(": "),
          )
          .join("; ")
      } else if (detail != null) {
        message = JSON.stringify(detail)
      }
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
}): Promise<PagedResult<ImportBatchOut>> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/imports?${qs}`)
  const total = Number(res.headers.get("X-Total-Count") ?? "0")
  return { data: await res.json(), total }
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
  search?: string
  category_id?: string
  uncategorized?: boolean
  limit?: number
  offset?: number
}): Promise<PagedResult<BankTransactionOut>> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.date_from) qs.set("date_from", params.date_from)
  if (params.date_to) qs.set("date_to", params.date_to)
  if (params.search) qs.set("search", params.search)
  if (params.category_id) qs.set("category_id", params.category_id)
  if (params.uncategorized) qs.set("uncategorized", "true")
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/bank-transactions?${qs}`)
  const total = Number(res.headers.get("X-Total-Count") ?? "0")
  return { data: await res.json(), total }
}

// ---------------------------------------------------------------------------
// Card transactions
// ---------------------------------------------------------------------------

export async function getCardTransactions(params: {
  instrument_id?: string
  date_from?: string
  date_to?: string
  search?: string
  category_id?: string
  uncategorized?: boolean
  limit?: number
  offset?: number
}): Promise<PagedResult<CardTransactionOut>> {
  const qs = new URLSearchParams()
  if (params.instrument_id) qs.set("instrument_id", params.instrument_id)
  if (params.date_from) qs.set("date_from", params.date_from)
  if (params.date_to) qs.set("date_to", params.date_to)
  if (params.search) qs.set("search", params.search)
  if (params.category_id) qs.set("category_id", params.category_id)
  if (params.uncategorized) qs.set("uncategorized", "true")
  if (params.limit != null) qs.set("limit", String(params.limit))
  if (params.offset != null) qs.set("offset", String(params.offset))
  const res = await apiFetch(`/card-transactions?${qs}`)
  const total = Number(res.headers.get("X-Total-Count") ?? "0")
  return { data: await res.json(), total }
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

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------

export async function getCategories(): Promise<CategoryOut[]> {
  const res = await apiFetch("/categories")
  return res.json()
}

export async function createCategory(data: CategoryCreate): Promise<CategoryOut> {
  const res = await apiFetch("/categories", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function updateCategory(id: string, data: CategoryUpdate): Promise<CategoryOut> {
  const res = await apiFetch(`/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function deleteCategory(id: string): Promise<void> {
  await apiFetch(`/categories/${id}`, { method: "DELETE" })
}

// ---------------------------------------------------------------------------
// Categorizations
// ---------------------------------------------------------------------------

export async function categorize(data: CategorizeRequest): Promise<CategorizationOut> {
  const res = await apiFetch("/categorize", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function bulkCategorize(data: BulkCategorizeRequest): Promise<BulkCategorizeResult> {
  const res = await apiFetch("/categorize/bulk", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function deleteCategorization(id: string): Promise<void> {
  await apiFetch(`/categorizations/${id}`, { method: "DELETE" })
}

// ---------------------------------------------------------------------------
// Category rules
// ---------------------------------------------------------------------------

export async function getCategoryRules(): Promise<CategoryRuleOut[]> {
  const res = await apiFetch("/category-rules")
  return res.json()
}

export async function createCategoryRule(data: CategoryRuleCreate): Promise<CategoryRuleOut> {
  const res = await apiFetch("/category-rules", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function updateCategoryRule(id: string, data: CategoryRuleUpdate): Promise<CategoryRuleOut> {
  const res = await apiFetch(`/category-rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function deleteCategoryRule(id: string): Promise<void> {
  await apiFetch(`/category-rules/${id}`, { method: "DELETE" })
}

export async function applyRules(): Promise<ApplyRulesResult> {
  const res = await apiFetch("/category-rules/apply", { method: "POST" })
  return res.json()
}

export async function dryRunRules(): Promise<DryRunResult> {
  const res = await apiFetch("/category-rules/dry-run", { method: "POST" })
  return res.json()
}

// ---------------------------------------------------------------------------
// Budget planning
// ---------------------------------------------------------------------------

export interface BudgetPeriodOut {
  id: string
  year: number
  month: number
  status: "open" | "closed"
  created_at: string
}

export interface CategoryBudgetItemOut {
  id: string
  budget_period_id: string
  category_id: string
  category_name: string
  category_kind: "expense" | "income" | "transfer"
  planned_amount_minor: number
  actual_amount_minor: number
  remaining_amount_minor: number
  pct_consumed: number
}

export interface BudgetDetailOut {
  id: string
  year: number
  month: number
  status: "open" | "closed"
  created_at: string
  planned_total_minor: number
  actual_total_minor: number
  remaining_total_minor: number
  pct_consumed: number
  items: CategoryBudgetItemOut[]
}

export interface BudgetPeriodCreate {
  year: number
  month: number
}

export interface CategoryBudgetCreate {
  category_id: string
  planned_amount_minor: number
}

export interface CategoryBudgetUpdate {
  planned_amount_minor: number
}

export async function getBudgetPeriods(): Promise<BudgetPeriodOut[]> {
  const res = await apiFetch("/budgets/periods")
  return res.json()
}

export async function createBudgetPeriod(data: BudgetPeriodCreate): Promise<BudgetPeriodOut> {
  const res = await apiFetch("/budgets/periods", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function getBudgetDetail(periodId: string): Promise<BudgetDetailOut> {
  const res = await apiFetch(`/budgets/${periodId}`)
  return res.json()
}

export async function upsertCategoryBudget(
  periodId: string,
  data: CategoryBudgetCreate,
): Promise<CategoryBudgetItemOut> {
  const res = await apiFetch(`/budgets/${periodId}/categories`, {
    method: "POST",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function updateCategoryBudgetItem(
  itemId: string,
  data: CategoryBudgetUpdate,
): Promise<CategoryBudgetItemOut> {
  const res = await apiFetch(`/budgets/category-items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function copyBudgetFrom(
  targetPeriodId: string,
  sourcePeriodId: string,
): Promise<BudgetDetailOut> {
  const res = await apiFetch(`/budgets/${targetPeriodId}/copy-from/${sourcePeriodId}`, {
    method: "POST",
  })
  return res.json()
}
