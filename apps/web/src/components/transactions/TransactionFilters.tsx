"use client"

import { useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { InstrumentPicker } from "@/components/instruments/InstrumentPicker"
import { useCategories } from "@/hooks/useCategories"
import type { InstrumentType } from "@/lib/api"

interface Props {
  typeFilter?: InstrumentType
}

export function TransactionFilters({ typeFilter }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: categories = [] } = useCategories()

  const instrumentId = searchParams.get("instrument_id") ?? undefined
  const dateFrom = searchParams.get("date_from") ?? ""
  const dateTo = searchParams.get("date_to") ?? ""
  const search = searchParams.get("search") ?? ""
  const categoryId = searchParams.get("category_id") ?? ""

  const update = useCallback(
    (key: string, value: string | undefined) => {
      const params = new URLSearchParams(searchParams.toString())
      if (value) params.set(key, value)
      else params.delete(key)
      params.delete("page")
      router.replace(`/transactions?${params}`)
    },
    [router, searchParams],
  )

  const hasFilters = !!(instrumentId || dateFrom || dateTo || search || categoryId)

  function clearAll() {
    const params = new URLSearchParams(searchParams.toString())
    params.delete("instrument_id")
    params.delete("date_from")
    params.delete("date_to")
    params.delete("search")
    params.delete("category_id")
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
          allLabel="All instruments"
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
        placeholder="Search description…"
        aria-label="Search transactions"
        className="h-9 w-full sm:w-52 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />

      <select
        value={categoryId}
        onChange={(e) => update("category_id", e.target.value || undefined)}
        aria-label="Filter by category"
        className="h-9 w-full sm:w-44 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <option value="">All categories</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {cat.name}
          </option>
        ))}
      </select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearAll} className="gap-1 text-muted-foreground">
          <X className="h-3.5 w-3.5" />
          Clear
        </Button>
      )}
    </div>
  )
}
