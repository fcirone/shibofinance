"use client"

import { useQuery } from "@tanstack/react-query"
import { getBankTransactions } from "@/lib/api"

interface Params {
  instrument_id?: string
  date_from?: string
  date_to?: string
  search?: string
  category_id?: string
  uncategorized?: boolean
  limit?: number
  offset?: number
}

export function useBankTransactions(params: Params = {}) {
  return useQuery({
    queryKey: ["bank-transactions", params],
    queryFn: () => getBankTransactions({ limit: 50, ...params }),
    staleTime: 0,
  })
}
