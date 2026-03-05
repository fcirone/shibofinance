"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getInstruments,
  createInstrument,
  updateInstrument,
  type InstrumentCreate,
  type InstrumentUpdate,
} from "@/lib/api"

export const INSTRUMENTS_KEY = ["instruments"] as const

export function useInstruments() {
  return useQuery({
    queryKey: INSTRUMENTS_KEY,
    queryFn: getInstruments,
    staleTime: 30_000,
  })
}

export function useCreateInstrument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: InstrumentCreate) => createInstrument(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: INSTRUMENTS_KEY }),
  })
}

export function useUpdateInstrument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InstrumentUpdate }) =>
      updateInstrument(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: INSTRUMENTS_KEY }),
  })
}
