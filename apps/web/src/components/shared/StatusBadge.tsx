import { Badge } from "@/components/ui/badge"
import type { ImportStatus, StatementStatus } from "@/lib/api"

const IMPORT_STATUS: Record<ImportStatus, { label: string; className: string }> = {
  processed: { label: "Processed", className: "bg-green-100 text-green-800 border-green-200" },
  failed:    { label: "Failed",    className: "bg-red-100 text-red-800 border-red-200" },
  created:   { label: "Pending",   className: "bg-yellow-100 text-yellow-800 border-yellow-200" },
}

const STATEMENT_STATUS: Record<StatementStatus, { label: string; className: string }> = {
  open:    { label: "Open",    className: "bg-blue-100 text-blue-800 border-blue-200" },
  paid:    { label: "Paid",    className: "bg-green-100 text-green-800 border-green-200" },
  partial: { label: "Partial", className: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  closed:  { label: "Closed",  className: "bg-gray-100 text-gray-700 border-gray-200" },
}

export function ImportStatusBadge({ status }: { status: ImportStatus }) {
  const { label, className } = IMPORT_STATUS[status] ?? { label: status, className: "" }
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  )
}

export function StatementStatusBadge({ status }: { status: StatementStatus }) {
  const { label, className } = STATEMENT_STATUS[status] ?? { label: status, className: "" }
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  )
}
