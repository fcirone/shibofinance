"use client"

import { useQuery } from "@tanstack/react-query"
import { getSpendingSummary } from "@/lib/api"

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export function useSpendingSummary(params: { date_from: string; date_to: string; instrument_id?: string }) {
  return useQuery({
    queryKey: ["spending-summary", params],
    queryFn: () => getSpendingSummary(params),
    staleTime: 0,
    enabled: ISO_DATE.test(params.date_from) && ISO_DATE.test(params.date_to),
  })
}
