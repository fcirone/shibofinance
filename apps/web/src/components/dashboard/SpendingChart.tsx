"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { BarChart2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatUSD } from "@/lib/utils"
import { useExchangeRates, toUSDMinor } from "@/hooks/useExchangeRates"
import type { SpendingSummaryOut } from "@/lib/api"

const COLORS = [
  "#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd",
  "#818cf8", "#4f46e5", "#7c3aed", "#9333ea",
]

interface Props {
  summary?: SpendingSummaryOut
  loading: boolean
}

interface ChartEntry {
  name: string
  usd: number  // minor units in USD
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload as ChartEntry
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      <p className="font-medium">{d.name}</p>
      <p className="text-muted-foreground">{formatUSD(d.usd)}</p>
    </div>
  )
}

export function SpendingChart({ summary, loading }: Props) {
  const { data: fx } = useExchangeRates()

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Spending by Category (USD)</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    )
  }

  const entries: ChartEntry[] = []

  if (summary && fx) {
    // Merge entries with the same category_name (may differ by currency)
    const byName = new Map<string, number>()
    for (const cat of summary.by_category) {
      if (cat.category_kind === "income") continue
      const usd = toUSDMinor(cat.total_minor, cat.currency, fx.rates) ?? 0
      byName.set(cat.category_name, (byName.get(cat.category_name) ?? 0) + usd)
    }
    const sorted = [...byName.entries()].sort((a, b) => b[1] - a[1])
    for (const [name, usd] of sorted) {
      if (usd > 0) entries.push({ name, usd })
    }
    if (summary.uncategorized_minor > 0) {
      const usd = toUSDMinor(summary.uncategorized_minor, "BRL", fx.rates)
      if (usd != null) entries.push({ name: "Uncategorized", usd })
    }
  }

  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Spending by Category (USD)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12 gap-3 text-center">
          <BarChart2 className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            {!fx ? "Loading exchange rates…" : "No spending data for this period."}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Spending by Category (USD)</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={Math.max(180, entries.length * 36)}>
          <BarChart
            data={entries}
            layout="vertical"
            margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
          >
            <XAxis
              type="number"
              tickFormatter={(v) => formatUSD(v)}
              tick={{ fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              tick={{ fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))" }} />
            <Bar dataKey="usd" radius={[0, 4, 4, 0]}>
              {entries.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
