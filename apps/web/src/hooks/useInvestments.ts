"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  AssetCreate,
  AssetPositionCreate,
  AssetPositionUpdate,
  InvestmentAccountCreate,
  createAsset,
  createAssetPosition,
  createInvestmentAccount,
  deleteAssetPosition,
  getAssetHistory,
  getAssetPositions,
  getAssets,
  getInvestmentAccounts,
  getPortfolioHistory,
  getPortfolioSummary,
  recordSnapshot,
  updateAssetPosition,
} from "@/lib/api"

export function useInvestmentAccounts() {
  return useQuery({
    queryKey: ["investment-accounts"],
    queryFn: getInvestmentAccounts,
    staleTime: 30_000,
  })
}

export function useCreateInvestmentAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: InvestmentAccountCreate) => createInvestmentAccount(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["investment-accounts"] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary"] })
    },
  })
}

export function useAssets() {
  return useQuery({
    queryKey: ["assets"],
    queryFn: getAssets,
    staleTime: 30_000,
  })
}

export function useCreateAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: AssetCreate) => createAsset(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets"] })
    },
  })
}

export function useAssetPositions(investment_account_id?: string) {
  return useQuery({
    queryKey: ["asset-positions", investment_account_id],
    queryFn: () => getAssetPositions(investment_account_id),
    staleTime: 0,
  })
}

export function useCreateAssetPosition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: AssetPositionCreate) => createAssetPosition(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["asset-positions"] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary"] })
    },
  })
}

export function useUpdateAssetPosition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AssetPositionUpdate }) => updateAssetPosition(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["asset-positions"] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary"] })
      qc.invalidateQueries({ queryKey: ["portfolio-history"] })
      qc.invalidateQueries({ queryKey: ["asset-history"] })
    },
  })
}

export function useDeleteAssetPosition() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAssetPosition(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["asset-positions"] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary"] })
      qc.invalidateQueries({ queryKey: ["portfolio-history"] })
      qc.invalidateQueries({ queryKey: ["asset-history"] })
    },
  })
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ["portfolio-summary"],
    queryFn: getPortfolioSummary,
    staleTime: 0,
  })
}

export function usePortfolioHistory(params?: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ["portfolio-history", params],
    queryFn: () => getPortfolioHistory(params),
    staleTime: 0,
  })
}

export function useAssetHistory(asset_id: string, params?: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ["asset-history", asset_id, params],
    queryFn: () => getAssetHistory(asset_id, params),
    staleTime: 0,
    enabled: !!asset_id,
  })
}

export function useRecordSnapshot() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: recordSnapshot,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolio-history"] })
      qc.invalidateQueries({ queryKey: ["asset-history"] })
      qc.invalidateQueries({ queryKey: ["portfolio-summary"] })
    },
  })
}
