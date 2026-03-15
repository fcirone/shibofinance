"use client"

import { useCallback } from "react"
import { useTranslations } from 'next-intl'
import { useRouter } from "@/i18n/navigation"
import { useSearchParams } from "next/navigation"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { InstrumentPicker } from "@/components/instruments/InstrumentPicker"
import { useCategories } from "@/hooks/useCategories"
import type { InstrumentType } from "@/lib/api"

interface Props {
  typeFilter?: InstrumentType
}

export function TransactionFilters({ typeFilter }: Props) {
  const t = useTranslations('transactions')
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: categories = [] } = useCategories()

  const instrumentId = searchParams.get("instrument_id") ?? undefined
  const dateFrom = searchParams.get("date_from") ?? ""
  const dateTo = searchParams.get("date_to") ?? ""
  const search = searchParams.get("search") ?? ""
  const categoryId = searchParams.get("category_id") ?? ""
  const uncategorized = searchParams.get("uncategorized") === "true"

  const update = useCallback(
    (key: string, value: string | undefined) => {
      const params = new URLSearchParams(searchParams.toString())
      if (value) params.set(key, value)
      else params.delete(key)
      params.delete("page")
      router.replace(`/transactions?${params}` as '/transactions')
    },
    [router, searchParams],
  )

  function toggleUncategorized(checked: boolean) {
    const params = new URLSearchParams(searchParams.toString())
    if (checked) {
      params.set("uncategorized", "true")
      // Uncategorized is mutually exclusive with category_id filter
      params.delete("category_id")
    } else {
      params.delete("uncategorized")
    }
    params.delete("page")
    router.replace(`/transactions?${params}`)
  }

  const hasFilters = !!(instrumentId || dateFrom || dateTo || search || categoryId || uncategorized)

  function clearAll() {
    const params = new URLSearchParams(searchParams.toString())
    params.delete("instrument_id")
    params.delete("date_from")
    params.delete("date_to")
    params.delete("search")
    params.delete("category_id")
    params.delete("uncategorized")
    params.delete("page")
    router.replace(`/transactions?${params}`)
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="w-full sm:w-52">
        <InstrumentPicker
          value={instrumentId}
          onChange={(v) => update("instrument_id", v)}
          typeFilter={typeFilter}
          allowAll
        />
      </div>

      <input
        type="date"
        value={dateFrom}
        onChange={(e) => update("date_from", e.target.value || undefined)}
        className="h-9 w-full sm:w-auto rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        aria-label="Date from"
      />
      <input
        type="date"
        value={dateTo}
        onChange={(e) => update("date_to", e.target.value || undefined)}
        className="h-9 w-full sm:w-auto rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        aria-label="Date to"
      />

      <input
        type="search"
        value={search}
        onChange={(e) => update("search", e.target.value || undefined)}
        placeholder={t('searchPlaceholder')}
        aria-label={t('searchPlaceholder')}
        className="h-9 w-full sm:w-52 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />

      <select
        value={categoryId}
        onChange={(e) => update("category_id", e.target.value || undefined)}
        disabled={uncategorized}
        aria-label="Filter by category"
        className="h-9 w-full sm:w-44 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
      >
        <option value="">{t('allCategories')}</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {cat.name}
          </option>
        ))}
      </select>

      <label className="flex items-center gap-2 cursor-pointer select-none">
        <Checkbox
          checked={uncategorized}
          onCheckedChange={(v) => toggleUncategorized(v === true)}
          id="uncategorized-filter"
        />
        <span className="text-sm text-muted-foreground">{t('uncategorizedOnly')}</span>
      </label>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearAll} className="gap-1 text-muted-foreground">
          <X className="h-3.5 w-3.5" />
          {t('clearFilters')}
        </Button>
      )}
    </div>
  )
}
