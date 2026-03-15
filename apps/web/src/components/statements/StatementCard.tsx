"use client"

import { useTranslations } from 'next-intl'
import { CalendarDays } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { StatementStatusBadge } from "@/components/shared/StatusBadge"
import { AmountDisplay } from "@/components/shared/AmountDisplay"
import { formatDate } from "@/lib/utils"
import type { CardStatementOut } from "@/lib/api"

interface Props {
  statement: CardStatementOut
  onClick?: () => void
}

export function StatementCard({ statement, onClick }: Props) {
  const t = useTranslations('statements')
  return (
    <Card
      className={onClick ? "cursor-pointer hover:bg-accent/40 transition-colors" : undefined}
      onClick={onClick}
    >
      <CardContent className="p-4 flex gap-3 items-start">
        <div className="mt-0.5 text-muted-foreground shrink-0">
          <CalendarDays className="h-5 w-5" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium">
              {formatDate(statement.statement_start)} – {formatDate(statement.statement_end)}
            </p>
            <StatementStatusBadge status={statement.status} />
          </div>

          {statement.due_date && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {t('due')} {formatDate(statement.due_date)}
            </p>
          )}
        </div>

        <div className="shrink-0 text-right">
          <AmountDisplay minor={statement.total_minor} currency={statement.currency} />
        </div>
      </CardContent>
    </Card>
  )
}
