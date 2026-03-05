"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createCategory,
  deleteCategory,
  getCategories,
  updateCategory,
  type CategoryCreate,
  type CategoryUpdate,
} from "@/lib/api"

const KEY = ["categories"] as const

export function useCategories() {
  return useQuery({
    queryKey: KEY,
    queryFn: getCategories,
    staleTime: 30_000,
  })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CategoryCreate) => createCategory(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useUpdateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) =>
      updateCategory(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}

export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteCategory(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  })
}
