"use client"

import { useQuery } from "@tanstack/react-query"
import { getCardTransactions } from "@/lib/api"

interface Params {
  instrument_id?: string
  date_from?: string
  date_to?: string
  search?: string
  category_id?: string
  limit?: number
  offset?: number
}

export function useCardTransactions(params: Params = {}) {
  return useQuery({
    queryKey: ["card-transactions", params],
    queryFn: () => getCardTransactions({ limit: 50, ...params }),
    staleTime: 0,
  })
}
