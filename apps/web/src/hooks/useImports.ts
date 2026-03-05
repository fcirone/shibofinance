"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getImports, getImportBatch, uploadFile } from "@/lib/api"
import type { ImportBatchOut } from "@/lib/api"

const IMPORTS_KEY = ["imports"] as const

export function useImports(params: { instrument_id?: string; limit?: number; offset?: number } = {}) {
  return useQuery({
    queryKey: [...IMPORTS_KEY, params],
    queryFn: () => getImports({ limit: 50, ...params }),
    staleTime: 0,
  })
}

export function useImportBatch(id: string | null) {
  return useQuery({
    queryKey: [...IMPORTS_KEY, id],
    queryFn: () => getImportBatch(id!),
    enabled: !!id,
    staleTime: 0,
  })
}

export function useUploadFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ instrumentId, file }: { instrumentId: string; file: File }) =>
      uploadFile(instrumentId, file),
    onSuccess: (batch: ImportBatchOut) => {
      qc.invalidateQueries({ queryKey: IMPORTS_KEY })
      return batch
    },
  })
}
