"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  copyBudgetFrom,
  createBudgetPeriod,
  getBudgetDetail,
  getBudgetPeriods,
  updateCategoryBudgetItem,
  upsertCategoryBudget,
  type BudgetPeriodCreate,
  type CategoryBudgetCreate,
  type CategoryBudgetUpdate,
} from "@/lib/api"

export function useBudgetPeriods() {
  return useQuery({
    queryKey: ["budget-periods"],
    queryFn: getBudgetPeriods,
    staleTime: 0,
  })
}

export function useBudgetDetail(periodId: string | undefined) {
  return useQuery({
    queryKey: ["budget-detail", periodId],
    queryFn: () => getBudgetDetail(periodId!),
    staleTime: 0,
    enabled: Boolean(periodId),
  })
}

export function useCreateBudgetPeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: BudgetPeriodCreate) => createBudgetPeriod(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["budget-periods"] }),
  })
}

export function useUpsertCategoryBudget(periodId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CategoryBudgetCreate) => upsertCategoryBudget(periodId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["budget-detail", periodId] }),
  })
}

export function useUpdateCategoryBudgetItem(periodId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: CategoryBudgetUpdate }) =>
      updateCategoryBudgetItem(itemId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["budget-detail", periodId] }),
  })
}

export function useCopyBudgetFrom(targetPeriodId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sourcePeriodId: string) => copyBudgetFrom(targetPeriodId, sourcePeriodId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["budget-detail", targetPeriodId] })
    },
  })
}
