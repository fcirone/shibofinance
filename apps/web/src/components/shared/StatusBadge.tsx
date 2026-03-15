"use client"

import { useTranslations } from 'next-intl'
import { Badge } from "@/components/ui/badge"
import type { ImportStatus, StatementStatus } from "@/lib/api"

const IMPORT_STATUS_CLASS: Record<ImportStatus, string> = {
  processed: "bg-green-100 text-green-800 border-green-200",
  failed:    "bg-red-100 text-red-800 border-red-200",
  created:   "bg-yellow-100 text-yellow-800 border-yellow-200",
}

const STATEMENT_STATUS_CLASS: Record<StatementStatus, string> = {
  open:    "bg-blue-100 text-blue-800 border-blue-200",
  paid:    "bg-green-100 text-green-800 border-green-200",
  partial: "bg-yellow-100 text-yellow-800 border-yellow-200",
  closed:  "bg-gray-100 text-gray-700 border-gray-200",
}

export function ImportStatusBadge({ status }: { status: ImportStatus }) {
  const t = useTranslations('status')
  const className = IMPORT_STATUS_CLASS[status] ?? ""
  const label = status === "created" ? t('created') : status === "processed" ? t('processed') : t('failed')
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  )
}

export function StatementStatusBadge({ status }: { status: StatementStatus }) {
  const t = useTranslations('status')
  const className = STATEMENT_STATUS_CLASS[status] ?? ""
  const labelMap: Record<StatementStatus, string> = {
    open: t('open'),
    closed: t('closed'),
    paid: t('paid'),
    partial: t('partial'),
  }
  return (
    <Badge variant="outline" className={className}>
      {labelMap[status] ?? status}
    </Badge>
  )
}
