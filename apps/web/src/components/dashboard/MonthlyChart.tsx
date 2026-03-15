"use client"

import { useQueries } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, CartesianGrid,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatUSD } from "@/lib/utils"
import { useExchangeRates, toUSDMinor } from "@/hooks/useExchangeRates"
import { getSpendingSummary } from "@/lib/api"

// ── helpers ───────────────────────────────────────────────────────────────────

function getLast12Months() {
  const now = new Date()
  const months: { label: string; date_from: string; date_to: string }[] = []
  for (let i = 11; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const y = d.getFullYear()
    const m = d.getMonth() + 1
    const pad = String(m).padStart(2, "0")
    const lastDay = new Date(y, m, 0).getDate()
    months.push({
      label: d.toLocaleDateString("en-US", { month: "short", year: "2-digit" }),
      date_from: `${y}-${pad}-01`,
      date_to: `${y}-${pad}-${lastDay}`,
    })
  }
  return months
}

const MONTHS = getLast12Months()

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md space-y-1">
      <p className="font-medium mb-1">{label}</p>
      {payload.map((p: { name: string; value: number; color: string }) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {formatUSD(p.value)}
        </p>
      ))}
    </div>
  )
}

// ── component ─────────────────────────────────────────────────────────────────

export function MonthlyChart() {
  const t = useTranslations('dashboard')
  const { data: fx } = useExchangeRates()

  const results = useQueries({
    queries: MONTHS.map((m) => ({
      queryKey: ["spending-summary", { date_from: m.date_from, date_to: m.date_to }],
      queryFn: () => getSpendingSummary({ date_from: m.date_from, date_to: m.date_to }),
      staleTime: 30 * 60 * 1000,
    })),
  })

  const isLoading = results.some((r) => r.isLoading)

  const creditsLabel = t('credits')
  const debitsLabel = t('debits')

  const entries = MONTHS.map((m, i) => {
    const summary = results[i].data
    let credits = 0
    let debits = 0
    if (summary && fx) {
      for (const cat of summary.by_category) {
        const usd = toUSDMinor(cat.total_minor, cat.currency, fx.rates) ?? 0
        if (cat.category_kind === "income") credits += usd
        else if (cat.category_kind === "expense") debits += usd
      }
      for (const [cur, amt] of Object.entries(summary.uncategorized_by_currency)) {
        debits += toUSDMinor(amt, cur, fx.rates) ?? 0
      }
      for (const [cur, amt] of Object.entries(summary.uncategorized_income_by_currency)) {
        credits += toUSDMinor(amt, cur, fx.rates) ?? 0
      }
    }
    return { label: m.label, [creditsLabel]: credits, [debitsLabel]: debits }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{t('creditsVsDebits')}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || !fx ? (
          <Skeleton className="h-52 w-full" />
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={entries} margin={{ top: 4, right: 8, bottom: 0, left: 8 }} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => formatUSD(v)}
                tick={{ fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={72}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted))" }} />
              <Legend iconType="square" iconSize={10} wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey={creditsLabel} fill="#22c55e" radius={[3, 3, 0, 0]} />
              <Bar dataKey={debitsLabel} fill="#f87171" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
