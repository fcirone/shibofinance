"use client"

export const dynamic = 'force-dynamic'

import { useState } from "react"
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { useSearchParams } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import {
  CheckCircle2,
  XCircle,
  Plus,
  Zap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { formatAmount } from "@/lib/utils"
import type { OccurrenceStatus, PayableOccurrenceOut } from "@/lib/api"
import {
  usePayableOccurrences,
  useGenerateOccurrences,
  useUpdateOccurrence,
  useCreatePayable,
} from "@/hooks/usePayables"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseMonth(param: string | null): { month: number; year: number } {
  if (param) {
    const [y, m] = param.split("-").map(Number)
    if (y && m && m >= 1 && m <= 12) return { year: y, month: m }
  }
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

function formatMonth(year: number, month: number) {
  return `${year}-${String(month).padStart(2, "0")}`
}

function shiftMonth(year: number, month: number, delta: number) {
  let m = month + delta
  let y = year
  if (m > 12) { m -= 12; y++ }
  if (m < 1) { m += 12; y-- }
  return { year: y, month: m }
}

function StatusBadgeCell({ status }: { status: OccurrenceStatus }) {
  const t = useTranslations('payables')
  const variantMap: Record<OccurrenceStatus, "default" | "secondary" | "destructive" | "outline"> = {
    expected: "secondary",
    pending:  "outline",
    paid:     "default",
    ignored:  "destructive",
  }
  const labelMap: Record<OccurrenceStatus, string> = {
    expected: t('expected'),
    pending:  t('pending'),
    paid:     t('paid'),
    ignored:  t('ignored'),
  }
  return <Badge variant={variantMap[status] ?? "secondary"}>{labelMap[status] ?? status}</Badge>
}

// ---------------------------------------------------------------------------
// Add payable dialog
// ---------------------------------------------------------------------------

const addSchema = z.object({
  name: z.string().min(1, "Name is required"),
  default_amount_minor: z.coerce.number().int().min(0).optional(),
  notes: z.string().optional(),
})
type AddForm = z.infer<typeof addSchema>

function AddPayableDialog({ onSuccess }: { onSuccess: () => void }) {
  const t = useTranslations('payables')
  const tc = useTranslations('common')
  const [open, setOpen] = useState(false)
  const create = useCreatePayable()
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<any>({ resolver: zodResolver(addSchema) })

  async function onSubmit(data: AddForm) {
    try {
      await create.mutateAsync({
        name: data.name,
        default_amount_minor: data.default_amount_minor ?? null,
        notes: data.notes || null,
      })
      toast.success(t('payableCreated'))
      setOpen(false)
      form.reset()
      onSuccess()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('payableCreateFailed'))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1.5" />
          {t('addPayable')}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>{t('newPayable')}</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="name">{t('payableName')}</Label>
            <Input id="name" placeholder={t('payableNamePlaceholder')} {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message as string}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="amount">{t('defaultAmountLabel')}</Label>
            <Input
              id="amount"
              type="number"
              placeholder="e.g. 9990"
              {...form.register("default_amount_minor")}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notes">{t('notesLabel')}</Label>
            <Input id="notes" placeholder={t('notesPlaceholder')} {...form.register("notes")} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {tc('cancel')}
            </Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {tc('create')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Occurrence row
// ---------------------------------------------------------------------------

function OccurrenceRow({
  occurrence,
  month,
  year,
}: {
  occurrence: PayableOccurrenceOut
  month: number
  year: number
}) {
  const t = useTranslations('payables')
  const update = useUpdateOccurrence(month, year)

  async function markPaid() {
    try {
      await update.mutateAsync({ id: occurrence.id, data: { status: "paid" } })
      toast.success(t('markedPaid'))
    } catch {
      toast.error(t('markPaidFailed'))
    }
  }

  async function markIgnored() {
    try {
      await update.mutateAsync({ id: occurrence.id, data: { status: "ignored" } })
      toast.success(t('ignore'))
    } catch {
      toast.error(t('markPaidFailed'))
    }
  }

  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
      <td className="py-3 px-4 text-[13px] font-medium">{occurrence.payable_name}</td>
      <td className="py-3 px-4 text-[13px] text-muted-foreground">
        {new Date(occurrence.due_date).toLocaleDateString()}
      </td>
      <td className="py-3 px-4 text-[13px] font-mono">
        {formatAmount(occurrence.expected_amount_minor, "BRL")}
      </td>
      <td className="py-3 px-4 text-[13px] font-mono">
        {occurrence.actual_amount_minor != null
          ? formatAmount(occurrence.actual_amount_minor, "BRL")
          : "—"}
      </td>
      <td className="py-3 px-4"><StatusBadgeCell status={occurrence.status} /></td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-1.5">
          {occurrence.status !== "paid" && occurrence.status !== "ignored" && (
            <>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                title={t('markPaid')}
                onClick={markPaid}
                disabled={update.isPending}
              >
                <CheckCircle2 className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                title={t('ignore')}
                onClick={markIgnored}
                disabled={update.isPending}
              >
                <XCircle className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const MONTH_NAMES_KEYS = [
  "january", "february", "march", "april", "may", "june",
  "july", "august", "september", "october", "november", "december",
] as const

export default function PayablesPage() {
  const t = useTranslations('payables')
  const tc = useTranslations('common')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { month, year } = parseMonth(searchParams.get("period"))

  const { data: occurrences, isLoading } = usePayableOccurrences(month, year)
  const generate = useGenerateOccurrences()

  function navigateMonth(delta: number) {
    const next = shiftMonth(year, month, delta)
    const params = new URLSearchParams(searchParams.toString())
    params.set("period", formatMonth(next.year, next.month))
    router.push(`${pathname}?${params}` as '/payables')
  }

  async function handleGenerate() {
    try {
      const res = await generate.mutateAsync({ month, year })
      toast.success(`Generated ${res.created} occurrence${res.created !== 1 ? "s" : ""}${res.skipped ? ` (${res.skipped} skipped)` : ""}`)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('generateFailed'))
    }
  }

  const monthName = tc(MONTH_NAMES_KEYS[month - 1])

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t('title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {t('subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AddPayableDialog onSuccess={() => {}} />
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerate}
            disabled={generate.isPending}
          >
            <Zap className="h-4 w-4 mr-1.5" />
            {t('generate')}
          </Button>
        </div>
      </div>

      {/* Month selector */}
      <div className="flex items-center gap-2 self-start">
        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => navigateMonth(-1)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-[14px] font-medium min-w-[130px] text-center">
          {monthName} {year}
        </span>
        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => navigateMonth(1)}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border overflow-hidden bg-card">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : !occurrences || occurrences.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center px-4">
            <CalendarCheck className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm font-medium text-muted-foreground">{t('noPayablesForMonth', { month: monthName, year })}</p>
            <p className="text-xs text-muted-foreground/70">
              {t('noPayablesDesc')}
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('name')}</th>
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('dueDate')}</th>
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('expectedAmount')}</th>
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('actualAmount')}</th>
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('status')}</th>
                <th className="py-2.5 px-4 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {occurrences.map((o) => (
                <OccurrenceRow key={o.id} occurrence={o} month={month} year={year} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function CalendarCheck(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18M9 16l2 2 4-4" />
    </svg>
  )
}
