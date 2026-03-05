"use client"

import Link from "next/link"
import { ExternalLink } from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { ImportStatusBadge } from "@/components/shared/StatusBadge"
import { Button } from "@/components/ui/button"
import { formatDate, formatDateTime } from "@/lib/utils"
import type { ImportBatchOut, InstrumentOut } from "@/lib/api"

interface Props {
  batch: ImportBatchOut | null
  instrument?: InstrumentOut
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

export function BatchDetailDrawer({ batch, instrument, open, onOpenChange }: Props) {
  if (!batch) return null

  const txLink = instrument
    ? `/transactions?instrument_id=${instrument.id}`
    : "/transactions"

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader className="mb-4">
          <SheetTitle className="text-base truncate">{batch.filename}</SheetTitle>
        </SheetHeader>

        <div className="space-y-0.5">
          <Row label="Status">
            <ImportStatusBadge status={batch.status} />
          </Row>
          {instrument && <Row label="Instrument">{instrument.name}</Row>}
          <Row label="Imported">{formatDateTime(batch.created_at)}</Row>
          {batch.processed_at && (
            <Row label="Processed">{formatDateTime(batch.processed_at)}</Row>
          )}
          <Row label="Inserted">{batch.inserted_count}</Row>
          <Row label="Duplicates">{batch.duplicate_count}</Row>
          {batch.error_count > 0 && (
            <Row label="Errors">
              <span className="text-destructive">{batch.error_count}</span>
            </Row>
          )}
          <Row label="SHA-256">
            <span className="font-mono text-xs break-all">{batch.sha256.slice(0, 16)}…</span>
          </Row>
        </div>

        <div className="mt-6">
          <Button asChild variant="outline" className="w-full" size="sm">
            <Link href={txLink} onClick={() => onOpenChange(false)}>
              <ExternalLink className="h-4 w-4 mr-2" />
              View transactions
            </Link>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
