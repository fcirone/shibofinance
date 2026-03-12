"use client"

import { FileText, CheckCircle2, Copy, AlertCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { ImportStatusBadge } from "@/components/shared/StatusBadge"
import { formatDateTime } from "@/lib/utils"
import type { ImportBatchOut, InstrumentOut } from "@/lib/api"

interface Props {
  batch: ImportBatchOut
  instrument?: InstrumentOut
  onClick?: () => void
}

export function ImportBatchCard({ batch, instrument, onClick }: Props) {
  return (
    <Card
      className={onClick ? "cursor-pointer hover:bg-accent/40 transition-colors" : undefined}
      onClick={onClick}
    >
      <CardContent className="p-4 flex gap-3 items-start">
        <div className="mt-0.5 text-muted-foreground shrink-0">
          <FileText className="h-5 w-5" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium truncate">{batch.filename}</p>
            <ImportStatusBadge status={batch.status} />
          </div>

          {instrument && (
            <p className="text-xs text-muted-foreground mt-0.5">{instrument.name}</p>
          )}

          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1 text-teal-500 dark:text-teal-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {batch.inserted_count} inserted
            </span>
            <span className="flex items-center gap-1">
              <Copy className="h-3.5 w-3.5" />
              {batch.duplicate_count} duplicates
            </span>
            {batch.error_count > 0 && (
              <span className="flex items-center gap-1 text-destructive">
                <AlertCircle className="h-3.5 w-3.5" />
                {batch.error_count} errors
              </span>
            )}
          </div>
        </div>

        <div className="text-xs text-muted-foreground shrink-0 text-right">
          {formatDateTime(batch.created_at)}
        </div>
      </CardContent>
    </Card>
  )
}
