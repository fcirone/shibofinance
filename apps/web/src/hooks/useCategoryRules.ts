"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getCategoryRules,
  createCategoryRule,
  updateCategoryRule,
  deleteCategoryRule,
  applyRules,
  dryRunRules,
} from "@/lib/api"

export function useCategoryRules() {
  return useQuery({ queryKey: ["category-rules"], queryFn: getCategoryRules, staleTime: 0 })
}

export function useCreateCategoryRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createCategoryRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["category-rules"] }),
  })
}

export function useUpdateCategoryRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updateCategoryRule>[1] }) =>
      updateCategoryRule(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["category-rules"] }),
  })
}

export function useDeleteCategoryRule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteCategoryRule,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["category-rules"] }),
  })
}

export function useApplyRules() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: applyRules,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bank-transactions"] })
      qc.invalidateQueries({ queryKey: ["card-transactions"] })
    },
  })
}

export function useDryRunRules() {
  return useMutation({ mutationFn: dryRunRules })
}
