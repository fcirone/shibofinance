"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  approveRecurringPattern,
  createPayable,
  detectRecurringPatterns,
  generateOccurrences,
  getPayableOccurrences,
  getPayables,
  getRecurringPatterns,
  ignoreRecurringPattern,
  updateOccurrence,
  type OccurrenceStatus,
  type OccurrenceUpdate,
  type PayableCreate,
  type RecurringPatternStatus,
} from "@/lib/api"

export function useRecurringPatterns(status?: RecurringPatternStatus) {
  return useQuery({
    queryKey: ["recurring-patterns", status ?? "all"],
    queryFn: () => getRecurringPatterns(status),
    staleTime: 0,
  })
}

export function useDetectRecurringPatterns() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: detectRecurringPatterns,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recurring-patterns"] }),
  })
}

export function useApprovePattern() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => approveRecurringPattern(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recurring-patterns"] }),
  })
}

export function useIgnorePattern() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => ignoreRecurringPattern(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recurring-patterns"] }),
  })
}

export function usePayables() {
  return useQuery({
    queryKey: ["payables"],
    queryFn: getPayables,
    staleTime: 30_000,
  })
}

export function useCreatePayable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PayableCreate) => createPayable(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payables"] }),
  })
}

export function usePayableOccurrences(month: number, year: number, status?: OccurrenceStatus) {
  return useQuery({
    queryKey: ["payable-occurrences", year, month, status ?? "all"],
    queryFn: () => getPayableOccurrences(month, year, status),
    staleTime: 0,
  })
}

export function useGenerateOccurrences() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ month, year }: { month: number; year: number }) => generateOccurrences(month, year),
    onSuccess: (_data, { month, year }) =>
      qc.invalidateQueries({ queryKey: ["payable-occurrences", year, month] }),
  })
}

export function useUpdateOccurrence(month: number, year: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: OccurrenceUpdate }) => updateOccurrence(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["payable-occurrences", year, month] }),
  })
}
