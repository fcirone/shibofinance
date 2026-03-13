"use client"

import { useState, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { toast } from "sonner"
import {
  Target,
  TrendingDown,
  Wallet,
  PlusCircle,
  Copy,
  Pencil,
  Check,
  X,
} from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  useBudgetPeriods,
  useBudgetDetail,
  useCreateBudgetPeriod,
  useUpsertCategoryBudget,
  useUpdateCategoryBudgetItem,
  useCopyBudgetFrom,
} from "@/hooks/useBudgets"
import { useCategories } from "@/hooks/useCategories"
import { cn, formatAmount } from "@/lib/utils"
import type { CategoryBudgetItemOut, BudgetPeriodOut } from "@/lib/api"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function currentYearMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
}

function parseYearMonth(ym: string): { year: number; month: number } | null {
  const m = ym.match(/^(\d{4})-(\d{2})$/)
  if (!m) return null
  const year = parseInt(m[1], 10)
  const month = parseInt(m[2], 10)
  if (month < 1 || month > 12) return null
  return { year, month }
}

function periodLabel(year: number, month: number) {
  return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  })
}

function formatMinor(minor: number) {
  // Display in a generic currency-agnostic way (minor units / 100)
  const val = (minor / 100).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return val
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  icon: Icon,
  label,
  value,
  valueClass,
  loading,
}: {
  icon: React.ElementType
  label: string
  value: string
  valueClass?: string
  loading: boolean
}) {
  return (
    <Card>
      <CardContent className="p-6 flex items-start gap-4">
        <div className="rounded-md bg-muted p-2 shrink-0">
          <Icon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        </div>
        <div className="space-y-1 min-w-0">
          <p className="text-sm text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="h-6 w-28" />
          ) : (
            <p className={cn("text-xl font-semibold tabular-nums", valueClass)}>{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function ProgressBar({ pct }: { pct: number }) {
  const capped = Math.min(pct, 100)
  const isOver = pct > 100
  return (
    <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
      <div
        className={cn(
          "h-full rounded-full transition-all duration-300",
          isOver ? "bg-destructive" : pct >= 80 ? "bg-amber-500" : "bg-primary",
        )}
        style={{ width: `${capped}%` }}
      />
    </div>
  )
}

function InlineAmountEditor({
  itemId,
  current,
  periodId,
  onClose,
}: {
  itemId: string
  current: number
  periodId: string
  onClose: () => void
}) {
  const [val, setVal] = useState(String(current / 100))
  const update = useUpdateCategoryBudgetItem(periodId)

  async function handleSave() {
    const parsed = parseFloat(val)
    if (isNaN(parsed) || parsed < 0) {
      toast.error("Enter a valid positive amount")
      return
    }
    try {
      await update.mutateAsync({ itemId, data: { planned_amount_minor: Math.round(parsed * 100) } })
      toast.success("Budget updated")
      onClose()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to update")
    }
  }

  return (
    <div className="flex items-center gap-1">
      <input
        autoFocus
        type="number"
        min="0"
        step="0.01"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSave()
          if (e.key === "Escape") onClose()
        }}
        className="w-24 text-sm border rounded px-2 py-0.5 bg-background focus:outline-none focus:ring-1 focus:ring-ring tabular-nums"
      />
      <Button
        size="icon"
        variant="ghost"
        className="h-6 w-6"
        onClick={handleSave}
        disabled={update.isPending}
        aria-label="Save"
      >
        <Check className="h-3.5 w-3.5" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className="h-6 w-6"
        onClick={onClose}
        aria-label="Cancel"
      >
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}

function BudgetRow({
  item,
  periodId,
}: {
  item: CategoryBudgetItemOut
  periodId: string
}) {
  const [editing, setEditing] = useState(false)
  const isOver = item.actual_amount_minor > item.planned_amount_minor && item.planned_amount_minor > 0

  return (
    <TableRow>
      <TableCell className="font-medium">
        {item.category_name}
        <span className="ml-2 hidden sm:inline">
          <Badge variant="outline" className="text-[10px] py-0">
            {item.category_kind}
          </Badge>
        </span>
      </TableCell>
      <TableCell className="text-right tabular-nums">
        {editing ? (
          <InlineAmountEditor
            itemId={item.id}
            current={item.planned_amount_minor}
            periodId={periodId}
            onClose={() => setEditing(false)}
          />
        ) : (
          <div className="flex items-center justify-end gap-1 group">
            <span>{formatMinor(item.planned_amount_minor)}</span>
            <Button
              size="icon"
              variant="ghost"
              className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={() => setEditing(true)}
              aria-label="Edit planned amount"
            >
              <Pencil className="h-3 w-3" />
            </Button>
          </div>
        )}
      </TableCell>
      <TableCell className="text-right tabular-nums hidden sm:table-cell">
        <span className={cn(item.actual_amount_minor > 0 ? "text-foreground" : "text-muted-foreground")}>
          {formatMinor(item.actual_amount_minor)}
        </span>
      </TableCell>
      <TableCell className="text-right tabular-nums hidden md:table-cell">
        <span className={cn(isOver ? "text-destructive font-medium" : "text-foreground")}>
          {isOver ? "-" : ""}{formatMinor(Math.abs(item.remaining_amount_minor))}
        </span>
      </TableCell>
      <TableCell className="w-32 hidden lg:table-cell">
        <div className="flex items-center gap-2">
          <ProgressBar pct={item.pct_consumed} />
          <span className={cn("text-xs tabular-nums shrink-0", isOver ? "text-destructive" : "text-muted-foreground")}>
            {item.pct_consumed.toFixed(0)}%
          </span>
        </div>
      </TableCell>
      <TableCell className="hidden lg:table-cell">
        {isOver && (
          <Badge variant="destructive" className="text-[10px]">Over</Badge>
        )}
        {!isOver && item.pct_consumed >= 80 && item.pct_consumed < 100 && (
          <Badge className="text-[10px] bg-amber-500 hover:bg-amber-500">Near limit</Badge>
        )}
      </TableCell>
    </TableRow>
  )
}

// ---------------------------------------------------------------------------
// Add Category Budget Dialog
// ---------------------------------------------------------------------------

function AddCategoryDialog({
  open,
  onOpenChange,
  periodId,
  existingCategoryIds,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  periodId: string
  existingCategoryIds: string[]
}) {
  const { data: categories = [] } = useCategories()
  const [categoryId, setCategoryId] = useState("")
  const [amount, setAmount] = useState("")
  const upsert = useUpsertCategoryBudget(periodId)

  const expenseCategories = categories.filter(
    (c) => c.kind === "expense" && !existingCategoryIds.includes(c.id),
  )

  async function handleSubmit() {
    if (!categoryId || !amount) {
      toast.error("Select a category and enter an amount")
      return
    }
    const parsed = parseFloat(amount)
    if (isNaN(parsed) || parsed < 0) {
      toast.error("Enter a valid positive amount")
      return
    }
    try {
      await upsert.mutateAsync({
        category_id: categoryId,
        planned_amount_minor: Math.round(parsed * 100),
      })
      toast.success("Category budget added")
      setCategoryId("")
      setAmount("")
      onOpenChange(false)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to add")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Category Budget</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Category</label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger>
                <SelectValue placeholder="Select expense category…" />
              </SelectTrigger>
              <SelectContent>
                {expenseCategories.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
                {expenseCategories.length === 0 && (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    No more expense categories available
                  </div>
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Planned amount</label>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full text-sm border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-2 focus:ring-ring tabular-nums"
            />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={upsert.isPending}>
              Add
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Copy-from Dialog
// ---------------------------------------------------------------------------

function CopyFromDialog({
  open,
  onOpenChange,
  targetPeriodId,
  periods,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  targetPeriodId: string
  periods: BudgetPeriodOut[]
}) {
  const [sourcePeriodId, setSourcePeriodId] = useState("")
  const copy = useCopyBudgetFrom(targetPeriodId)

  const otherPeriods = periods.filter((p) => p.id !== targetPeriodId)

  async function handleCopy() {
    if (!sourcePeriodId) {
      toast.error("Select a period to copy from")
      return
    }
    try {
      await copy.mutateAsync(sourcePeriodId)
      toast.success("Budget copied")
      setSourcePeriodId("")
      onOpenChange(false)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to copy")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Copy Budget From</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <Select value={sourcePeriodId} onValueChange={setSourcePeriodId}>
            <SelectTrigger>
              <SelectValue placeholder="Select source month…" />
            </SelectTrigger>
            <SelectContent>
              {otherPeriods.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {periodLabel(p.year, p.month)}
                </SelectItem>
              ))}
              {otherPeriods.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">No other periods available</div>
              )}
            </SelectContent>
          </Select>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleCopy} disabled={copy.isPending}>
              Copy
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Create Period Dialog
// ---------------------------------------------------------------------------

function CreatePeriodDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  const [ym, setYm] = useState(currentYearMonth())
  const create = useCreateBudgetPeriod()
  const router = useRouter()
  const searchParams = useSearchParams()

  async function handleCreate() {
    const parsed = parseYearMonth(ym)
    if (!parsed) {
      toast.error("Invalid month")
      return
    }
    try {
      const period = await create.mutateAsync(parsed)
      toast.success("Budget period created")
      onOpenChange(false)
      // Navigate to the new period
      const params = new URLSearchParams(searchParams.toString())
      params.set("period", `${period.year}-${String(period.month).padStart(2, "0")}`)
      router.replace(`/planning?${params}`)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to create period")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Create Budget Period</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Month</label>
            <input
              type="month"
              value={ym}
              onChange={(e) => setYm(e.target.value)}
              className="w-full text-sm border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={create.isPending}>
              Create
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PlanningPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const periodParam = searchParams.get("period") ?? currentYearMonth()
  const parsed = parseYearMonth(periodParam)

  const { data: periods = [], isLoading: periodsLoading } = useBudgetPeriods()

  // Find the period that matches the URL param
  const activePeriod = periods.find(
    (p) => parsed && p.year === parsed.year && p.month === parsed.month,
  )

  const { data: detail, isLoading: detailLoading } = useBudgetDetail(activePeriod?.id)

  const [createOpen, setCreateOpen] = useState(false)
  const [addCatOpen, setAddCatOpen] = useState(false)
  const [copyOpen, setCopyOpen] = useState(false)

  const setPeriodParam = useCallback(
    (ym: string) => {
      const params = new URLSearchParams(searchParams.toString())
      params.set("period", ym)
      router.replace(`/planning?${params}`)
    },
    [router, searchParams],
  )

  const isLoading = periodsLoading || (Boolean(activePeriod) && detailLoading)

  return (
    <>
      <PageHeader
        title="Planning"
        action={
          <Button onClick={() => setCreateOpen(true)} size="sm">
            <PlusCircle className="h-4 w-4 mr-1.5" />
            New period
          </Button>
        }
      />

      {/* Period selector */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground shrink-0">Month</label>
          <input
            type="month"
            value={periodParam}
            onChange={(e) => setPeriodParam(e.target.value)}
            className="text-sm border rounded-md px-2 py-1.5 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        {periods.length > 0 && (
          <div className="w-48">
            <Select
              value={activePeriod?.id ?? ""}
              onValueChange={(id) => {
                const p = periods.find((x) => x.id === id)
                if (p) setPeriodParam(`${p.year}-${String(p.month).padStart(2, "0")}`)
              }}
            >
              <SelectTrigger className="text-sm h-8">
                <SelectValue placeholder="Jump to period…" />
              </SelectTrigger>
              <SelectContent>
                {periods.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {periodLabel(p.year, p.month)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* No periods at all */}
      {!periodsLoading && periods.length === 0 && (
        <EmptyState
          icon={Target}
          title="No budgets yet"
          description="Create a monthly budget to start planning your spending by category."
          action={{ label: "Create first budget", onClick: () => setCreateOpen(true) }}
        />
      )}

      {/* Period exists in list but not in DB yet for this month */}
      {!periodsLoading && periods.length > 0 && !activePeriod && (
        <EmptyState
          icon={Target}
          title="No budget for this month"
          description={`There is no budget for ${parsed ? periodLabel(parsed.year, parsed.month) : periodParam} yet.`}
          action={{ label: "Create budget", onClick: () => setCreateOpen(true) }}
        />
      )}

      {/* Period exists — show detail */}
      {activePeriod && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <StatCard
              icon={Target}
              label="Planned"
              value={isLoading ? "—" : formatMinor(detail?.planned_total_minor ?? 0)}
              loading={isLoading}
            />
            <StatCard
              icon={TrendingDown}
              label="Actual"
              value={isLoading ? "—" : formatMinor(detail?.actual_total_minor ?? 0)}
              valueClass={
                detail && detail.actual_total_minor > detail.planned_total_minor && detail.planned_total_minor > 0
                  ? "text-destructive"
                  : undefined
              }
              loading={isLoading}
            />
            <StatCard
              icon={Wallet}
              label="Remaining"
              value={isLoading ? "—" : formatMinor(Math.abs(detail?.remaining_total_minor ?? 0))}
              valueClass={
                detail && detail.remaining_total_minor < 0 ? "text-destructive" : "text-teal-500 dark:text-teal-400"
              }
              loading={isLoading}
            />
          </div>

          {/* Overall progress bar */}
          {!isLoading && detail && detail.planned_total_minor > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-muted-foreground">Overall consumption</span>
                <span
                  className={cn(
                    "text-sm font-medium tabular-nums",
                    detail.pct_consumed > 100 ? "text-destructive" : "text-foreground",
                  )}
                >
                  {detail.pct_consumed.toFixed(1)}%
                </span>
              </div>
              <ProgressBar pct={detail.pct_consumed} />
            </div>
          )}

          {/* Category table */}
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Category Breakdown
            </h2>
            <div className="flex items-center gap-2">
              {periods.length > 1 && (
                <Button variant="outline" size="sm" onClick={() => setCopyOpen(true)}>
                  <Copy className="h-3.5 w-3.5 mr-1.5" />
                  Copy from month
                </Button>
              )}
              <Button size="sm" onClick={() => setAddCatOpen(true)}>
                <PlusCircle className="h-3.5 w-3.5 mr-1.5" />
                Add category
              </Button>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))}
            </div>
          ) : !detail || detail.items.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              No category budgets yet.{" "}
              <button
                className="underline underline-offset-2 hover:text-foreground transition-colors"
                onClick={() => setAddCatOpen(true)}
              >
                Add a category
              </button>{" "}
              to start planning.
            </div>
          ) : (
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Planned</TableHead>
                    <TableHead className="text-right hidden sm:table-cell">Actual</TableHead>
                    <TableHead className="text-right hidden md:table-cell">Remaining</TableHead>
                    <TableHead className="hidden lg:table-cell w-36">Progress</TableHead>
                    <TableHead className="hidden lg:table-cell w-20">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detail.items
                    .filter((item) => item.category_kind === "expense")
                    .sort((a, b) => b.planned_amount_minor - a.planned_amount_minor)
                    .map((item) => (
                      <BudgetRow key={item.id} item={item} periodId={activePeriod.id} />
                    ))}
                  {/* Non-expense rows dimmed at bottom */}
                  {detail.items
                    .filter((item) => item.category_kind !== "expense")
                    .map((item) => (
                      <BudgetRow key={item.id} item={item} periodId={activePeriod.id} />
                    ))}
                </TableBody>
              </Table>
            </div>
          )}
        </>
      )}

      {/* Dialogs */}
      <CreatePeriodDialog open={createOpen} onOpenChange={setCreateOpen} />
      {activePeriod && (
        <>
          <AddCategoryDialog
            open={addCatOpen}
            onOpenChange={setAddCatOpen}
            periodId={activePeriod.id}
            existingCategoryIds={detail?.items.map((i) => i.category_id) ?? []}
          />
          <CopyFromDialog
            open={copyOpen}
            onOpenChange={setCopyOpen}
            targetPeriodId={activePeriod.id}
            periods={periods}
          />
        </>
      )}
    </>
  )
}
