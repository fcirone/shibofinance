"use client"

import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from "recharts"
import { BarChart2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useExchangeRates, toUSDMinor } from "@/hooks/useExchangeRates"
import type { SpendingSummaryOut } from "@/lib/api"

const COLORS = [
  "#6366f1", "#8b5cf6", "#a78bfa", "#818cf8",
  "#4f46e5", "#7c3aed", "#9333ea", "#c4b5fd",
]

interface ChartEntry {
  name: string
  pct: number   // e.g. 42.5
  usd: number
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as ChartEntry
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md space-y-0.5">
      <p className="font-medium">{d.name}</p>
      <p className="text-muted-foreground">{d.pct.toFixed(1)}% of income</p>
    </div>
  )
}

interface Props {
  summary?: SpendingSummaryOut
  loading: boolean
}

export function CategoryIncomeRatioChart({ summary, loading }: Props) {
  const { data: fx } = useExchangeRates()

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Spending as % of Income</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-52 w-full" />
        </CardContent>
      </Card>
    )
  }

  const entries: ChartEntry[] = []

  if (summary && fx) {
    let totalIncomeUSD = 0
    const expenseItems: { name: string; usd: number }[] = []

    const expenseByName = new Map<string, number>()
    for (const cat of summary.by_category) {
      const usd = toUSDMinor(cat.total_minor, cat.currency, fx.rates) ?? 0
      if (cat.category_kind === "income") {
        totalIncomeUSD += usd
      } else if (cat.category_kind === "expense") {
        expenseByName.set(cat.category_name, (expenseByName.get(cat.category_name) ?? 0) + usd)
      }
    }
    for (const [name, usd] of expenseByName.entries()) {
      expenseItems.push({ name, usd })
    }
    // Include uncategorized income in the denominator
    for (const [cur, amt] of Object.entries(summary.uncategorized_income_by_currency)) {
      totalIncomeUSD += toUSDMinor(amt, cur, fx.rates) ?? 0
    }
    // Include uncategorized expenses as a bucket
    const uncatExpense = toUSDMinor(summary.uncategorized_minor, "BRL", fx.rates) ?? 0
    if (uncatExpense > 0) expenseItems.push({ name: "Uncategorized", usd: uncatExpense })

    if (totalIncomeUSD > 0) {
      expenseItems.sort((a, b) => b.usd - a.usd)
      for (const item of expenseItems) {
        entries.push({ name: item.name, pct: (item.usd / totalIncomeUSD) * 100, usd: item.usd })
      }
    }
  }

  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Spending as % of Income</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12 gap-3 text-center">
          <BarChart2 className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            {!fx ? "Loading exchange rates…" : "No data for this period."}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Spending as % of Income</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={Math.max(200, entries.length * 34)}>
          <BarChart
            data={entries}
            layout="vertical"
            margin={{ top: 0, right: 48, bottom: 0, left: 8 }}
          >
            <XAxis
              type="number"
              domain={[0, Math.max(100, Math.ceil(Math.max(...entries.map((e) => e.pct)) / 10) * 10)]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={110}
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <ReferenceLine x={100} stroke="hsl(var(--destructive))" strokeDasharray="4 2" strokeWidth={1.5} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))" }} />
            <Bar dataKey="pct" radius={[0, 4, 4, 0]} label={{ position: "right", fontSize: 11, formatter: (v: unknown) => `${Number(v).toFixed(0)}%` }}>
              {entries.map((e, i) => (
                <Cell key={e.name} fill={e.pct > 100 ? "#f87171" : COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
