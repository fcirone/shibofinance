"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Receipt } from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { TableSkeleton } from "@/components/shared/LoadingSkeleton"
import { PaginationBar } from "@/components/shared/PaginationBar"
import { TransactionFilters } from "@/components/transactions/TransactionFilters"
import { TransactionsTable } from "@/components/transactions/TransactionsTable"
import { BulkCategoryBar } from "@/components/transactions/BulkCategoryBar"
import { useBankTransactions } from "@/hooks/useBankTransactions"
import { useCardTransactions } from "@/hooks/useCardTransactions"
import type { BankTransactionOut, CardTransactionOut, TargetType } from "@/lib/api"

const PAGE_SIZE = 50

export default function TransactionsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const tab = (searchParams.get("tab") ?? "bank") as "bank" | "card"
  const instrumentId = searchParams.get("instrument_id") ?? undefined
  const dateFrom = searchParams.get("date_from") ?? undefined
  const dateTo = searchParams.get("date_to") ?? undefined
  const search = searchParams.get("search") ?? undefined
  const categoryId = searchParams.get("category_id") ?? undefined
  const uncategorized = searchParams.get("uncategorized") === "true"
  const page = Math.max(1, Number(searchParams.get("page") ?? "1"))
  const offset = (page - 1) * PAGE_SIZE

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const bankQuery = useBankTransactions(
    tab === "bank"
      ? { instrument_id: instrumentId, date_from: dateFrom, date_to: dateTo, search, category_id: categoryId, uncategorized, limit: PAGE_SIZE, offset }
      : {},
  )
  const cardQuery = useCardTransactions(
    tab === "card"
      ? { instrument_id: instrumentId, date_from: dateFrom, date_to: dateTo, search, category_id: categoryId, uncategorized, limit: PAGE_SIZE, offset }
      : {},
  )

  const rows = tab === "bank" ? (bankQuery.data ?? []) : (cardQuery.data ?? [])
  const isLoading = tab === "bank" ? bankQuery.isLoading : cardQuery.isLoading
  const targetType: TargetType = tab === "bank" ? "bank_transaction" : "card_transaction"

  function switchTab(value: string) {
    setSelectedIds(new Set())
    const params = new URLSearchParams()
    params.set("tab", value)
    router.replace(`/transactions?${params}`)
  }

  return (
    <>
      <PageHeader title="Transactions" />

      <Tabs value={tab} onValueChange={switchTab} className="space-y-5">
        <TabsList>
          <TabsTrigger value="bank">Bank</TabsTrigger>
          <TabsTrigger value="card">Card</TabsTrigger>
        </TabsList>

        <TransactionFilters typeFilter={tab === "bank" ? "bank_account" : "credit_card"} />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="No transactions found"
            description="Try adjusting your filters or import a statement file."
          />
        ) : (
          <>
            <BulkCategoryBar
              selectedIds={selectedIds}
              targetType={targetType}
              onClear={() => setSelectedIds(new Set())}
            />
            {tab === "bank" ? (
              <TransactionsTable
                tab="bank"
                rows={rows as BankTransactionOut[]}
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
              />
            ) : (
              <TransactionsTable
                tab="card"
                rows={rows as CardTransactionOut[]}
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
              />
            )}
            <PaginationBar
              page={page}
              pageSize={PAGE_SIZE}
              count={rows.length}
              basePath="/transactions"
            />
          </>
        )}
      </Tabs>
    </>
  )
}
