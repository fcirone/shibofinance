"use client"

import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AmountDisplay } from "@/components/shared/AmountDisplay"
import { formatUSD, formatDate } from "@/lib/utils"
import { useExchangeRates, toUSDMinor } from "@/hooks/useExchangeRates"
import { CategoryPicker } from "./CategoryPicker"
import type { BankTransactionOut, CardTransactionOut } from "@/lib/api"

interface BankTableProps {
  tab: "bank"
  rows: BankTransactionOut[]
  selectedIds: Set<string>
  onSelectionChange: (ids: Set<string>) => void
}

interface CardTableProps {
  tab: "card"
  rows: CardTransactionOut[]
  selectedIds: Set<string>
  onSelectionChange: (ids: Set<string>) => void
}

type Props = BankTableProps | CardTableProps

function USDCell({ minor, currency, rates }: { minor: number; currency: string; rates: Record<string, number> | undefined }) {
  const usd = toUSDMinor(minor, currency, rates)
  if (usd == null) return <span className="text-muted-foreground text-xs">—</span>
  // If original is already USD, show value but dim it (same as Amount column)
  const isSame = currency === "USD"
  return (
    <span className={`font-mono tabular-nums text-xs ${usd < 0 ? "text-destructive/60" : isSame ? "text-muted-foreground/50" : "text-muted-foreground"}`}>
      {formatUSD(usd)}
    </span>
  )
}

export function TransactionsTable(props: Props) {
  const { rows, selectedIds, onSelectionChange } = props
  const { data: fx } = useExchangeRates()

  if (rows.length === 0) return null

  const allIds = rows.map((r) => r.id)
  const allSelected = allIds.length > 0 && allIds.every((id) => selectedIds.has(id))
  const someSelected = allIds.some((id) => selectedIds.has(id))

  function toggleAll() {
    if (allSelected) {
      const next = new Set(selectedIds)
      allIds.forEach((id) => next.delete(id))
      onSelectionChange(next)
    } else {
      const next = new Set(selectedIds)
      allIds.forEach((id) => next.add(id))
      onSelectionChange(next)
    }
  }

  function toggleRow(id: string) {
    const next = new Set(selectedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    onSelectionChange(next)
  }

  if (props.tab === "bank") {
    return (
      <div className="rounded-lg border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">
                <Checkbox
                  checked={allSelected ? true : someSelected ? "indeterminate" : false}
                  onCheckedChange={toggleAll}
                  aria-label="Select all"
                />
              </TableHead>
              <TableHead scope="col" className="w-28">Date</TableHead>
              <TableHead scope="col">Description</TableHead>
              <TableHead scope="col" className="hidden sm:table-cell">Category</TableHead>
              <TableHead scope="col" className="text-right w-36">Amount</TableHead>
              <TableHead scope="col" className="text-right w-28 hidden md:table-cell">≈ USD</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(rows as BankTransactionOut[]).map((tx) => (
              <TableRow key={tx.id} data-state={selectedIds.has(tx.id) ? "selected" : undefined}>
                <TableCell>
                  <Checkbox
                    checked={selectedIds.has(tx.id)}
                    onCheckedChange={() => toggleRow(tx.id)}
                    aria-label={`Select transaction ${tx.description_raw}`}
                  />
                </TableCell>
                <TableCell className="tabular-nums text-muted-foreground">
                  {formatDate(tx.posted_date)}
                </TableCell>
                <TableCell className="max-w-sm">
                  <p className="truncate text-sm">{tx.description_raw}</p>
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <CategoryPicker
                    targetType="bank_transaction"
                    targetId={tx.id}
                    categoryId={tx.category_id}
                    categoryName={tx.category_name}
                    categorySource={tx.category_source}
                    categoryRuleName={tx.category_rule_name}
                  />
                </TableCell>
                <TableCell className="text-right">
                  <AmountDisplay minor={tx.amount_minor} currency={tx.currency} />
                </TableCell>
                <TableCell className="text-right hidden md:table-cell">
                  <USDCell minor={tx.amount_minor} currency={tx.currency} rates={fx?.rates} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    )
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <Checkbox
                checked={allSelected ? true : someSelected ? "indeterminate" : false}
                onCheckedChange={toggleAll}
                aria-label="Select all"
              />
            </TableHead>
            <TableHead scope="col" className="w-28">Date</TableHead>
            <TableHead scope="col">Description</TableHead>
            <TableHead scope="col" className="hidden md:table-cell">Merchant</TableHead>
            <TableHead scope="col" className="hidden sm:table-cell">Category</TableHead>
            <TableHead scope="col" className="text-right w-36">Amount</TableHead>
            <TableHead scope="col" className="text-right w-28 hidden md:table-cell">≈ USD</TableHead>
            <TableHead scope="col" className="hidden sm:table-cell w-28">Installments</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(rows as CardTransactionOut[]).map((tx) => (
            <TableRow key={tx.id} data-state={selectedIds.has(tx.id) ? "selected" : undefined}>
              <TableCell>
                <Checkbox
                  checked={selectedIds.has(tx.id)}
                  onCheckedChange={() => toggleRow(tx.id)}
                  aria-label={`Select transaction ${tx.description_raw}`}
                />
              </TableCell>
              <TableCell className="tabular-nums text-muted-foreground">
                {formatDate(tx.posted_date)}
              </TableCell>
              <TableCell className="max-w-xs">
                <p className="truncate text-sm">{tx.description_raw}</p>
              </TableCell>
              <TableCell className="hidden md:table-cell text-muted-foreground text-sm">
                {tx.merchant_raw ?? "—"}
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                <CategoryPicker
                  targetType="card_transaction"
                  targetId={tx.id}
                  categoryId={tx.category_id}
                  categoryName={tx.category_name}
                  categorySource={tx.category_source}
                  categoryRuleName={tx.category_rule_name}
                />
              </TableCell>
              <TableCell className="text-right">
                <AmountDisplay minor={tx.amount_minor} currency={tx.currency} />
              </TableCell>
              <TableCell className="text-right hidden md:table-cell">
                <USDCell minor={tx.amount_minor} currency={tx.currency} rates={fx?.rates} />
              </TableCell>
              <TableCell className="hidden sm:table-cell text-center">
                {tx.installments_total && tx.installments_total > 1 ? (
                  <Badge variant="secondary" className="font-mono text-xs">
                    {tx.installment_number}/{tx.installments_total}
                  </Badge>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
