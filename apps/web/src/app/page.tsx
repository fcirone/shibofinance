"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Upload, List, CreditCard, ArrowRight } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/shared/PageHeader"
import { SummaryCards } from "@/components/dashboard/SummaryCards"
import { SpendingChart } from "@/components/dashboard/SpendingChart"
import { RecentImportsWidget } from "@/components/dashboard/RecentImportsWidget"
import { useSpendingSummary } from "@/hooks/useSpendingSummary"
import { useImports } from "@/hooks/useImports"
import { useInstruments } from "@/hooks/useInstruments"

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

// ── Onboarding ────────────────────────────────────────────────────────────────

function OnboardingPanel() {
  const router = useRouter()
  const steps = [
    { n: 1, label: "Add a bank account or credit card instrument", cta: "Add Instrument", href: "/instruments" },
    { n: 2, label: "Import a statement file (PDF or CSV)", cta: "Import File", href: "/import/new" },
    { n: 3, label: "Browse your transactions", cta: "View Transactions", href: "/transactions" },
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
          <div
            key={s.n}
            className="flex items-center gap-4 rounded-lg border bg-card p-4"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-semibold shrink-0">
              {s.n}
            </span>
            <p className="text-sm flex-1">{s.label}</p>
            <Button
              size="sm"
              variant="ghost"
              className="shrink-0"
              onClick={() => router.push(s.href)}
            >
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── QuickActions ──────────────────────────────────────────────────────────────

function QuickActions() {
  const router = useRouter()
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <Card
        className="cursor-pointer hover:bg-accent/40 transition-colors"
        onClick={() => router.push("/import/new")}
      >
        <CardContent className="p-6 flex items-center gap-4">
          <div className="rounded-md bg-muted p-2 shrink-0">
            <Upload className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium text-sm">Import a statement</p>
            <p className="text-xs text-muted-foreground">Upload a PDF or CSV file</p>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground ml-auto" />
        </CardContent>
      </Card>
      <Card
        className="cursor-pointer hover:bg-accent/40 transition-colors"
        onClick={() => router.push("/transactions")}
      >
        <CardContent className="p-6 flex items-center gap-4">
          <div className="rounded-md bg-muted p-2 shrink-0">
            <List className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium text-sm">Browse transactions</p>
            <p className="text-xs text-muted-foreground">Filter, search and paginate</p>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground ml-auto" />
        </CardContent>
      </Card>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [yearMonth, setYearMonth] = useState(currentYearMonth)
  const { date_from, date_to } = monthToRange(yearMonth)

  const { data: instruments = [], isLoading: instrumentsLoading } = useInstruments()
  const { data: summary, isLoading: summaryLoading } = useSpendingSummary({ date_from, date_to })
  const { data: recentImports = [], isLoading: importsLoading } = useImports({ limit: 5 })

  const lastImport = recentImports[0]

  // Onboarding: show if no instruments (and not still loading)
  if (!instrumentsLoading && instruments.length === 0) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <OnboardingPanel />
      </>
    )
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        action={
          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-muted-foreground" />
            <input
              type="month"
              value={yearMonth}
              onChange={(e) => setYearMonth(e.target.value)}
              className="text-sm border rounded-md px-2 py-1 bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        }
      />

      <div className="space-y-6">
        <SummaryCards
          summary={summary}
          lastImport={lastImport}
          summaryLoading={summaryLoading}
          importsLoading={importsLoading}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SpendingChart summary={summary} loading={summaryLoading} />
          </div>
          <div>
            <RecentImportsWidget />
          </div>
        </div>

        <QuickActions />
      </div>
    </>
  )
}
