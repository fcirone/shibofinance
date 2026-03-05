"use client"

import { useQuery } from "@tanstack/react-query"
import { getSpendingSummary } from "@/lib/api"

export function useSpendingSummary(params: { date_from: string; date_to: string; instrument_id?: string }) {
  return useQuery({
    queryKey: ["spending-summary", params],
    queryFn: () => getSpendingSummary(params),
    staleTime: 0,
    enabled: !!params.date_from && !!params.date_to,
  })
}
