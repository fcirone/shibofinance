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

// ---------------------------------------------------------------------------
// Payables and Recurring Patterns
// ---------------------------------------------------------------------------

export type RecurringCadence = "monthly" | "weekly" | "yearly" | "custom"
export type DetectionSource = "system" | "manual"
export type RecurringPatternStatus = "suggested" | "approved" | "ignored"
export type PayableSourceType = "manual" | "recurring_pattern"
export type OccurrenceStatus = "expected" | "pending" | "paid" | "ignored"

export interface RecurringPatternOut {
  id: string
  name: string
  normalized_description: string
  category_id: string | null
  category_name: string | null
  expected_amount_minor: number | null
  cadence: RecurringCadence
  detection_source: DetectionSource
  status: RecurringPatternStatus
  created_at: string
}

export interface RecurringPatternCreate {
  name: string
  normalized_description: string
  category_id?: string | null
  expected_amount_minor?: number | null
  cadence?: RecurringCadence
}

export interface DetectResult {
  created: number
  skipped: number
}

export interface PayableOut {
  id: string
  name: string
  category_id: string | null
  category_name: string | null
  default_amount_minor: number | null
  notes: string | null
  source_type: PayableSourceType
  recurring_pattern_id: string | null
  created_at: string
}

export interface PayableCreate {
  name: string
  category_id?: string | null
  default_amount_minor?: number | null
  notes?: string | null
}

export interface PayableOccurrenceOut {
  id: string
  payable_id: string
  payable_name: string
  due_date: string
  expected_amount_minor: number
  actual_amount_minor: number | null
  status: OccurrenceStatus
  notes: string | null
  created_at: string
}

export interface OccurrenceUpdate {
  status?: OccurrenceStatus | null
  actual_amount_minor?: number | null
  notes?: string | null
}

export interface GenerateOccurrencesResult {
  created: number
  skipped: number
}

export async function getRecurringPatterns(status?: RecurringPatternStatus): Promise<RecurringPatternOut[]> {
  const params = status ? `?status=${status}` : ""
  const res = await apiFetch(`/recurring-patterns${params}`)
  return res.json()
}

export async function detectRecurringPatterns(): Promise<DetectResult> {
  const res = await apiFetch("/recurring-patterns/detect", { method: "POST" })
  return res.json()
}

export async function approveRecurringPattern(id: string): Promise<RecurringPatternOut> {
  const res = await apiFetch(`/recurring-patterns/${id}/approve`, { method: "POST" })
  return res.json()
}

export async function ignoreRecurringPattern(id: string): Promise<RecurringPatternOut> {
  const res = await apiFetch(`/recurring-patterns/${id}/ignore`, { method: "POST" })
  return res.json()
}

export async function getPayables(): Promise<PayableOut[]> {
  const res = await apiFetch("/payables")
  return res.json()
}

export async function createPayable(data: PayableCreate): Promise<PayableOut> {
  const res = await apiFetch("/payables", { method: "POST", body: JSON.stringify(data) })
  return res.json()
}

export async function getPayableOccurrences(
  month: number,
  year: number,
  status?: OccurrenceStatus,
): Promise<PayableOccurrenceOut[]> {
  const params = new URLSearchParams({ month: String(month), year: String(year) })
  if (status) params.set("status", status)
  const res = await apiFetch(`/payable-occurrences?${params}`)
  return res.json()
}

export async function generateOccurrences(month: number, year: number): Promise<GenerateOccurrencesResult> {
  const res = await apiFetch("/payable-occurrences/generate", {
    method: "POST",
    body: JSON.stringify({ month, year }),
  })
  return res.json()
}

export async function updateOccurrence(id: string, data: OccurrenceUpdate): Promise<PayableOccurrenceOut> {
  const res = await apiFetch(`/payable-occurrences/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  })
  return res.json()
}

// ---------------------------------------------------------------------------
// Investments
// ---------------------------------------------------------------------------

export type AssetClass = "stock" | "bond" | "etf" | "real_estate" | "crypto" | "cash" | "other"

export interface InvestmentAccountOut {
  id: string
  name: string
  institution_name: string | null
  currency: string
  created_at: string
}

export interface InvestmentAccountCreate {
  name: string
  institution_name?: string | null
  currency?: string
}

export interface AssetOut {
  id: string
  symbol: string | null
  name: string
  asset_class: AssetClass
  currency: string
  created_at: string
}

export interface AssetCreate {
  symbol?: string | null
  name: string
  asset_class: AssetClass
  currency?: string
  metadata?: Record<string, unknown> | null
}

export interface AssetPositionOut {
  id: string
  investment_account_id: string
  asset_id: string
  asset_symbol: string | null
  asset_name: string
  asset_class: AssetClass
  quantity: number
  average_cost_minor: number | null
  current_value_minor: number | null
  as_of_date: string
  created_at: string
}

export interface AssetPositionCreate {
  investment_account_id: string
  asset_id: string
  quantity: number
  average_cost_minor?: number | null
  current_value_minor?: number | null
  as_of_date: string
}

export interface AssetPositionUpdate {
  quantity?: number | null
  average_cost_minor?: number | null
  current_value_minor?: number | null
  as_of_date?: string | null
}

export interface AllocationItem {
  asset_class: AssetClass
  total_value_minor: number
  pct: number
}

export interface AccountSummaryItem {
  account_id: string
  account_name: string
  currency: string
  total_value_minor: number
}

export interface PortfolioSummaryOut {
  total_value_minor: number
  accounts: AccountSummaryItem[]
  allocation: AllocationItem[]
}

export async function getInvestmentAccounts(): Promise<InvestmentAccountOut[]> {
  const res = await apiFetch("/investment-accounts")
  return res.json()
}

export async function createInvestmentAccount(data: InvestmentAccountCreate): Promise<InvestmentAccountOut> {
  const res = await apiFetch("/investment-accounts", { method: "POST", body: JSON.stringify(data) })
  return res.json()
}

export async function getAssets(): Promise<AssetOut[]> {
  const res = await apiFetch("/assets")
  return res.json()
}

export async function createAsset(data: AssetCreate): Promise<AssetOut> {
  const res = await apiFetch("/assets", { method: "POST", body: JSON.stringify(data) })
  return res.json()
}

export async function getAssetPositions(investment_account_id?: string): Promise<AssetPositionOut[]> {
  const params = investment_account_id ? `?investment_account_id=${investment_account_id}` : ""
  const res = await apiFetch(`/asset-positions${params}`)
  return res.json()
}

export async function createAssetPosition(data: AssetPositionCreate): Promise<AssetPositionOut> {
  const res = await apiFetch("/asset-positions", { method: "POST", body: JSON.stringify(data) })
  return res.json()
}

export async function updateAssetPosition(id: string, data: AssetPositionUpdate): Promise<AssetPositionOut> {
  const res = await apiFetch(`/asset-positions/${id}`, { method: "PATCH", body: JSON.stringify(data) })
  return res.json()
}

export async function getPortfolioSummary(): Promise<PortfolioSummaryOut> {
  const res = await apiFetch("/portfolio/summary")
  return res.json()
}
