"use client"

import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { AmountDisplay } from "@/components/shared/AmountDisplay"
import { formatDate } from "@/lib/utils"
import { CategoryPicker } from "./CategoryPicker"
import type { BankTransactionOut, CardTransactionOut } from "@/lib/api"

interface BankTableProps {
  tab: "bank"
  rows: BankTransactionOut[]
}

interface CardTableProps {
  tab: "card"
  rows: CardTransactionOut[]
}

type Props = BankTableProps | CardTableProps

export function TransactionsTable(props: Props) {
  if (props.rows.length === 0) return null

  if (props.tab === "bank") {
    return (
      <div className="rounded-lg border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col" className="w-28">Date</TableHead>
              <TableHead scope="col">Description</TableHead>
              <TableHead scope="col" className="hidden sm:table-cell">Category</TableHead>
              <TableHead scope="col" className="text-right w-36">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(props.rows as BankTransactionOut[]).map((tx) => (
              <TableRow key={tx.id}>
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
                  />
                </TableCell>
                <TableCell className="text-right">
                  <AmountDisplay minor={tx.amount_minor} currency={tx.currency} />
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
            <TableHead scope="col" className="w-28">Date</TableHead>
            <TableHead scope="col">Description</TableHead>
            <TableHead scope="col" className="hidden md:table-cell">Merchant</TableHead>
            <TableHead scope="col" className="hidden sm:table-cell">Category</TableHead>
            <TableHead scope="col" className="text-right w-36">Amount</TableHead>
            <TableHead scope="col" className="hidden sm:table-cell w-28">Installments</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(props.rows as CardTransactionOut[]).map((tx) => (
            <TableRow key={tx.id}>
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
                />
              </TableCell>
              <TableCell className="text-right">
                <AmountDisplay minor={tx.amount_minor} currency={tx.currency} />
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
