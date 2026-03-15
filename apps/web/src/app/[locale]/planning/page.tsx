"use client"

export const dynamic = 'force-dynamic'

import { useState, useCallback } from "react"
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { useSearchParams } from "next/navigation"
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
import { Card, CardContent } from "@/components/ui/card"
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
  const t = useTranslations('planning')
  const [val, setVal] = useState(String(current / 100))
  const update = useUpdateCategoryBudgetItem(periodId)

  async function handleSave() {
    const parsed = parseFloat(val)
    if (isNaN(parsed) || parsed < 0) {
      toast.error(t('invalidAmount'))
      return
    }
    try {
      await update.mutateAsync({ itemId, data: { planned_amount_minor: Math.round(parsed * 100) } })
      toast.success(t('budgetUpdated'))
      onClose()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('updateFailed'))
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
  const t = useTranslations('planning')
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
          <Badge variant="destructive" className="text-[10px]">{t('over')}</Badge>
        )}
        {!isOver && item.pct_consumed >= 80 && item.pct_consumed < 100 && (
          <Badge className="text-[10px] bg-amber-500 hover:bg-amber-500">{t('nearLimit')}</Badge>
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
  const t = useTranslations('planning')
  const tc = useTranslations('common')
  const { data: categories = [] } = useCategories()
  const [categoryId, setCategoryId] = useState("")
  const [amount, setAmount] = useState("")
  const upsert = useUpsertCategoryBudget(periodId)

  const expenseCategories = categories.filter(
    (c) => c.kind === "expense" && !existingCategoryIds.includes(c.id),
  )

  async function handleSubmit() {
    if (!categoryId || !amount) {
      toast.error(t('selectCategoryAndAmount'))
      return
    }
    const parsed = parseFloat(amount)
    if (isNaN(parsed) || parsed < 0) {
      toast.error(t('invalidAmount'))
      return
    }
    try {
      await upsert.mutateAsync({
        category_id: categoryId,
        planned_amount_minor: Math.round(parsed * 100),
      })
      toast.success(t('categoryAdded'))
      setCategoryId("")
      setAmount("")
      onOpenChange(false)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('addFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t('addCategoryBudget')}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t('category')}</label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger>
                <SelectValue placeholder={t('selectCategory')} />
              </SelectTrigger>
              <SelectContent>
                {expenseCategories.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
                {expenseCategories.length === 0 && (
                  <div className="px-3 py-2 text-sm text-muted-foreground">
                    {t('noCategoriesAvailable')}
                  </div>
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t('plannedAmount')}</label>
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
              {tc('cancel')}
            </Button>
            <Button onClick={handleSubmit} disabled={upsert.isPending}>
              {tc('add')}
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
  const t = useTranslations('planning')
  const tc = useTranslations('common')
  const [sourcePeriodId, setSourcePeriodId] = useState("")
  const copy = useCopyBudgetFrom(targetPeriodId)

  const otherPeriods = periods.filter((p) => p.id !== targetPeriodId)

  async function handleCopy() {
    if (!sourcePeriodId) {
      toast.error(t('selectPeriodToCopy'))
      return
    }
    try {
      await copy.mutateAsync(sourcePeriodId)
      toast.success(t('copiedFrom'))
      setSourcePeriodId("")
      onOpenChange(false)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('copyFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{t('copyBudget')}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <Select value={sourcePeriodId} onValueChange={setSourcePeriodId}>
            <SelectTrigger>
              <SelectValue placeholder={t('selectSourceMonth')} />
            </SelectTrigger>
            <SelectContent>
              {otherPeriods.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {periodLabel(p.year, p.month)}
                </SelectItem>
              ))}
              {otherPeriods.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">{t('noOtherPeriods')}</div>
              )}
            </SelectContent>
          </Select>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              {tc('cancel')}
            </Button>
            <Button onClick={handleCopy} disabled={copy.isPending}>
              {tc('copy')}
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
  const t = useTranslations('planning')
  const tc = useTranslations('common')
  const [ym, setYm] = useState(currentYearMonth())
  const create = useCreateBudgetPeriod()
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  async function handleCreate() {
    const parsed = parseYearMonth(ym)
    if (!parsed) {
      toast.error(t('invalidMonth'))
      return
    }
    try {
      const period = await create.mutateAsync(parsed)
      toast.success(t('budgetCreated'))
      onOpenChange(false)
      const params = new URLSearchParams(searchParams.toString())
      params.set("period", `${period.year}-${String(period.month).padStart(2, "0")}`)
      router.replace(`${pathname}?${params}` as '/planning')
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('createFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{t('newBudgetPeriod')}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">{t('month')}</label>
            <input
              type="month"
              value={ym}
              onChange={(e) => setYm(e.target.value)}
              className="w-full text-sm border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              {tc('cancel')}
            </Button>
            <Button onClick={handleCreate} disabled={create.isPending}>
              {tc('create')}
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
  const t = useTranslations('planning')
  const tc = useTranslations('common')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const periodParam = searchParams.get("period") ?? currentYearMonth()
  const parsed = parseYearMonth(periodParam)

  const { data: periods = [], isLoading: periodsLoading } = useBudgetPeriods()

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
      router.replace(`${pathname}?${params}` as '/planning')
    },
    [router, pathname, searchParams],
  )

  const isLoading = periodsLoading || (Boolean(activePeriod) && detailLoading)

  return (
    <>
      <PageHeader
        title={t('title')}
        action={
          <Button onClick={() => setCreateOpen(true)} size="sm">
            <PlusCircle className="h-4 w-4 mr-1.5" />
            {t('newPeriod')}
          </Button>
        }
      />

      {/* Period selector */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground shrink-0">{t('month')}</label>
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
                <SelectValue placeholder={t('jumpToPeriod')} />
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
          title={t('noBudgetsYet')}
          description={t('noBudgetsYetDesc')}
          action={{ label: t('createBudget'), onClick: () => setCreateOpen(true) }}
        />
      )}

      {/* Period exists in list but not in DB yet for this month */}
      {!periodsLoading && periods.length > 0 && !activePeriod && (
        <EmptyState
          icon={Target}
          title={t('noBudget')}
          description={t('noBudgetDesc')}
          action={{ label: t('createBudget'), onClick: () => setCreateOpen(true) }}
        />
      )}

      {/* Period exists — show detail */}
      {activePeriod && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <StatCard
              icon={Target}
              label={t('planned')}
              value={isLoading ? "—" : formatMinor(detail?.planned_total_minor ?? 0)}
              loading={isLoading}
            />
            <StatCard
              icon={TrendingDown}
              label={t('actual')}
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
              label={t('remaining')}
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
                <span className="text-sm text-muted-foreground">{t('overallConsumption')}</span>
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
              {t('categoryBreakdown')}
            </h2>
            <div className="flex items-center gap-2">
              {periods.length > 1 && (
                <Button variant="outline" size="sm" onClick={() => setCopyOpen(true)}>
                  <Copy className="h-3.5 w-3.5 mr-1.5" />
                  {t('copyFromMonth')}
                </Button>
              )}
              <Button size="sm" onClick={() => setAddCatOpen(true)}>
                <PlusCircle className="h-3.5 w-3.5 mr-1.5" />
                {t('addCategory')}
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
              {t('noCategoryBudgets')}{" "}
              <button
                className="underline underline-offset-2 hover:text-foreground transition-colors"
                onClick={() => setAddCatOpen(true)}
              >
                {t('addCategory')}
              </button>{" "}
              {t('noCategoryBudgetsAction')}
            </div>
          ) : (
            <div className="rounded-lg border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('category')}</TableHead>
                    <TableHead className="text-right">{t('planned')}</TableHead>
                    <TableHead className="text-right hidden sm:table-cell">{t('actual')}</TableHead>
                    <TableHead className="text-right hidden md:table-cell">{t('remaining')}</TableHead>
                    <TableHead className="hidden lg:table-cell w-36">{t('progress')}</TableHead>
                    <TableHead className="hidden lg:table-cell w-20">{t('status')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detail.items
                    .filter((item) => item.category_kind === "expense")
                    .sort((a, b) => b.planned_amount_minor - a.planned_amount_minor)
                    .map((item) => (
                      <BudgetRow key={item.id} item={item} periodId={activePeriod.id} />
                    ))}
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
