"use client"

import { useTranslations } from 'next-intl'
import { Link } from "@/i18n/navigation"
import { ExternalLink } from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { StatementStatusBadge } from "@/components/shared/StatusBadge"
import { AmountDisplay } from "@/components/shared/AmountDisplay"
import { Button } from "@/components/ui/button"
import { formatDate } from "@/lib/utils"
import type { CardStatementOut } from "@/lib/api"

interface Props {
  statement: CardStatementOut | null
  instrumentId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-2 border-b border-border/50 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-right">{children}</span>
    </div>
  )
}

export function StatementDetailDrawer({ statement, instrumentId, open, onOpenChange }: Props) {
  const t = useTranslations('statements')
  if (!statement) return null

  const params = new URLSearchParams({ tab: "card" })
  if (instrumentId) params.set("instrument_id", instrumentId)
  params.set("date_from", statement.statement_start)
  params.set("date_to", statement.statement_end)
  const txLink = `/transactions?${params}` as '/transactions'

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader className="mb-4">
          <SheetTitle className="text-base">
            {formatDate(statement.statement_start)} – {formatDate(statement.statement_end)}
          </SheetTitle>
        </SheetHeader>

        <div className="space-y-0.5">
          <Row label={t('statusLabel')}>
            <StatementStatusBadge status={statement.status} />
          </Row>
          <Row label={t('periodStart')}>{formatDate(statement.statement_start)}</Row>
          <Row label={t('periodEnd')}>{formatDate(statement.statement_end)}</Row>
          {statement.closing_date && (
            <Row label={t('closingDate')}>{formatDate(statement.closing_date)}</Row>
          )}
          {statement.due_date && (
            <Row label={t('dueDate')}>{formatDate(statement.due_date)}</Row>
          )}
          <Row label={t('total')}>
            <AmountDisplay minor={statement.total_minor} currency={statement.currency} />
          </Row>
          <Row label={t('currency')}>{statement.currency}</Row>
        </div>

        <div className="mt-6">
          <Button asChild variant="outline" className="w-full" size="sm">
            <Link href={txLink} onClick={() => onOpenChange(false)}>
              <ExternalLink className="h-4 w-4 mr-2" />
              {t('viewTransactions')}
            </Link>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
