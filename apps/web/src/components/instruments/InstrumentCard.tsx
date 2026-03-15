"use client"

import { useTranslations } from 'next-intl'
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { SourceBadge } from "@/components/shared/SourceBadge"
import { Pencil } from "lucide-react"
import { formatDate } from "@/lib/utils"
import type { InstrumentOut } from "@/lib/api"

interface InstrumentCardProps {
  instrument: InstrumentOut
  onEdit: (instrument: InstrumentOut) => void
}

export function InstrumentCard({ instrument, onEdit }: InstrumentCardProps) {
  const t = useTranslations('instruments')
  return (
    <Card className="flex flex-col gap-0">
      <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
        <div className="space-y-1 min-w-0">
          <p className="font-semibold text-base leading-tight truncate">
            {instrument.name}
          </p>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="secondary" className="text-xs">
              {instrument.type === "bank_account" ? t('bankAccount') : t('creditCard')}
            </Badge>
            <SourceBadge source={instrument.source} />
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 -mt-1 -mr-2"
          onClick={() => onEdit(instrument)}
          aria-label={`Edit ${instrument.name}`}
        >
          <Pencil className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground space-y-0.5">
        <p>
          <span className="font-medium text-foreground">{instrument.currency}</span>
        </p>
        <p className="text-xs">{t('addedOn', { date: formatDate(instrument.created_at.split("T")[0]) })}</p>
      </CardContent>
    </Card>
  )
}
