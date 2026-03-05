"use client"

import Link from "next/link"
import { FileText, ArrowRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ImportStatusBadge } from "@/components/shared/StatusBadge"
import { formatDateTime } from "@/lib/utils"
import { useImports } from "@/hooks/useImports"
import { useInstruments } from "@/hooks/useInstruments"

export function RecentImportsWidget() {
  const { data: batches = [], isLoading } = useImports({ limit: 5 })
  const { data: instruments = [] } = useInstruments()

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-sm font-medium">Recent Imports</CardTitle>
        <Link
          href="/imports"
          className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-4 w-4 rounded" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
          ))
        ) : batches.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">No imports yet.</p>
        ) : (
          batches.map((batch) => {
            const inst = instruments.find((i) => i.id === batch.instrument_id)
            return (
              <div key={batch.id} className="flex items-center gap-3 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="truncate font-medium">{batch.filename}</p>
                  {inst && <p className="text-xs text-muted-foreground">{inst.name}</p>}
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <ImportStatusBadge status={batch.status} />
                  <span className="text-xs text-muted-foreground">{formatDateTime(batch.created_at)}</span>
                </div>
              </div>
            )
          })
        )}
      </CardContent>
    </Card>
  )
}
