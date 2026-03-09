"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { SpendingChart } from "@/components/dashboard/SpendingChart"
import { MonthlyChart } from "@/components/dashboard/MonthlyChart"
import { CategoryIncomeRatioChart } from "@/components/dashboard/CategoryIncomeRatioChart"
import { useSpendingSummary } from "@/hooks/useSpendingSummary"
import { useInstruments } from "@/hooks/useInstruments"
import { useExchangeRates, toUSDMinor } from "@/hooks/useExchangeRates"
import { formatUSD } from "@/lib/utils"
import { cn } from "@/lib/utils"

// ── helpers ──────────────────────────────────────────────────────────────────

function currentYearMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
}

function monthToRange(ym: string): { date_from: string; date_to: string } {
  const [year, month] = ym.split("-").map(Number)
  const date_from = `${year}-${String(month).padStart(2, "0")}-01`
  const lastDay = new Date(year, month, 0).getDate()
  const date_to = `${year}-${String(month).padStart(2, "0")}-${lastDay}`
  return { date_from, date_to }
}

// ── Inline stat pill ──────────────────────────────────────────────────────────

function StatPill({
  label,
  value,
  loading,
  valueClass,
}: {
  label: string
  value: string
  loading: boolean
  valueClass?: string
}) {
  return (
    <div className="flex flex-col items-end">
      <span className="text-[11px] text-muted-foreground uppercase tracking-wide leading-none mb-0.5">
        {label}
      </span>
      {loading ? (
        <Skeleton className="h-5 w-24" />
      ) : (
        <span className={cn("text-base font-semibold tabular-nums leading-none", valueClass)}>
          {value}
        </span>
      )}
    </div>
  )
}

// ── Onboarding ────────────────────────────────────────────────────────────────

function OnboardingPanel() {
  const router = useRouter()
  const steps = [
    { n: 1, label: "Add a bank account or credit card instrument", href: "/instruments" },
    { n: 2, label: "Import a statement file (PDF or CSV)", href: "/import/new" },
    { n: 3, label: "Browse your transactions", href: "/transactions" },
  ]
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-8">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-semibold">Welcome to Shibo Finance</h2>
        <p className="text-muted-foreground text-sm max-w-sm">
          Get started by setting up your first instrument and importing a statement.
        </p>
      </div>
      <div className="w-full max-w-sm space-y-3">
        {steps.map((s) => (
          <div key={s.n} className="flex items-center gap-4 rounded-lg border bg-card p-4">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-semibold shrink-0">
              {s.n}
            </span>
            <p className="text-sm flex-1">{s.label}</p>
            <Button size="sm" variant="ghost" className="shrink-0" onClick={() => router.push(s.href)}>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [yearMonth, setYearMonth] = useState(currentYearMonth)
  const { date_from, date_to } = monthToRange(yearMonth)

  const { data: instruments = [], isLoading: instrumentsLoading } = useInstruments()
  const { data: summary, isLoading: summaryLoading } = useSpendingSummary({ date_from, date_to })
  const { data: fx } = useExchangeRates()

  // Compute credits, debits, balance in USD — include uncategorized amounts
  let creditsUSD = 0
  let debitsUSD = 0
  if (summary && fx) {
    for (const cat of summary.by_category) {
      const usd = toUSDMinor(cat.total_minor, cat.currency, fx.rates) ?? 0
      if (cat.category_kind === "income") creditsUSD += usd
      else if (cat.category_kind === "expense") debitsUSD += usd
    }
    // Uncategorized expenses (assumed BRL as fallback — same as before)
    debitsUSD += toUSDMinor(summary.uncategorized_minor, "BRL", fx.rates) ?? 0
    // Uncategorized income
    for (const [cur, amt] of Object.entries(summary.uncategorized_income_by_currency)) {
      creditsUSD += toUSDMinor(amt, cur, fx.rates) ?? 0
    }
  }
  const balanceUSD = creditsUSD - debitsUSD
  const statsLoading = summaryLoading || !fx

  // Onboarding: show if no instruments (and not still loading)
  if (!instrumentsLoading && instruments.length === 0) {
    return (
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>
        <OnboardingPanel />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* ── Header: title + period picker + stat pills ── */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <input
            type="month"
            value={yearMonth}
            onChange={(e) => setYearMonth(e.target.value)}
            className="text-sm border rounded-md px-2 py-1 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="flex items-center gap-6 border rounded-lg px-4 py-2 bg-card">
          <StatPill
            label="Credits"
            value={formatUSD(creditsUSD)}
            loading={statsLoading}
            valueClass="text-green-600 dark:text-green-400"
          />
          <div className="w-px h-8 bg-border" />
          <StatPill
            label="Debits"
            value={formatUSD(debitsUSD)}
            loading={statsLoading}
            valueClass="text-destructive"
          />
          <div className="w-px h-8 bg-border" />
          <StatPill
            label="Balance"
            value={formatUSD(balanceUSD)}
            loading={statsLoading}
            valueClass={balanceUSD >= 0 ? "text-green-600 dark:text-green-400" : "text-destructive"}
          />
        </div>
      </div>

      {/* ── Row 1: 12-month credits vs debits (full width) ── */}
      <MonthlyChart />

      {/* ── Row 2: Spending by category + Category % of income ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpendingChart summary={summary} loading={summaryLoading} />
        <CategoryIncomeRatioChart summary={summary} loading={summaryLoading} />
      </div>
    </div>
  )
}
