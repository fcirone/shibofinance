"use client"

import { TrendingDown, Receipt, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatAmount, formatDateTime } from "@/lib/utils"
import type { SpendingSummaryOut, ImportBatchOut } from "@/lib/api"

interface Props {
  summary?: SpendingSummaryOut
  lastImport?: ImportBatchOut
  summaryLoading: boolean
  importsLoading: boolean
}

function StatCard({
  icon: Icon,
  label,
  value,
  loading,
}: {
  icon: React.ElementType
  label: string
  value: React.ReactNode
  loading: boolean
}) {
  return (
    <Card>
      <CardContent className="p-6 flex items-start gap-4">
        <div className="rounded-md bg-muted p-2 shrink-0">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="h-6 w-28" />
          ) : (
            <p className="text-xl font-semibold tabular-nums">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function SummaryCards({ summary, lastImport, summaryLoading, importsLoading }: Props) {
  const totalExpenses = summary
    ? formatAmount(summary.total_minor, "BRL")
    : "—"

  const totalTxs = summary
    ? String(summary.by_category.reduce((acc, c) => acc + c.transaction_count, 0))
    : "—"

  const lastImportDate = lastImport ? formatDateTime(lastImport.created_at) : "—"

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        icon={TrendingDown}
        label="Total Expenses"
        value={totalExpenses}
        loading={summaryLoading}
      />
      <StatCard
        icon={Receipt}
        label="Transactions"
        value={totalTxs}
        loading={summaryLoading}
      />
      <StatCard
        icon={Clock}
        label="Last Import"
        value={lastImportDate}
        loading={importsLoading}
      />
    </div>
  )
}
