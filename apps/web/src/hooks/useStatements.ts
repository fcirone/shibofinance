"use client"

import { useQuery } from "@tanstack/react-query"
import { getCardStatements } from "@/lib/api"

const STATEMENTS_KEY = ["statements"] as const

export function useStatements(params: { instrument_id?: string } = {}) {
  return useQuery({
    queryKey: [...STATEMENTS_KEY, params],
    queryFn: () => getCardStatements(params),
    staleTime: 0,
  })
}
