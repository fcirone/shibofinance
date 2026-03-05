import { Badge } from "@/components/ui/badge"
import type { InstrumentSource } from "@/lib/api"

const SOURCE: Record<InstrumentSource, { label: string; className: string }> = {
  santander_br: { label: "Santander BR", className: "bg-red-100 text-red-800 border-red-200" },
  xp_br:        { label: "XP BR",        className: "bg-orange-100 text-orange-800 border-orange-200" },
  bbva_uy:      { label: "BBVA UY",      className: "bg-sky-100 text-sky-800 border-sky-200" },
}

export function SourceBadge({ source }: { source: InstrumentSource }) {
  const { label, className } = SOURCE[source] ?? { label: source, className: "" }
  return (
    <Badge variant="outline" className={className}>
      {label}
    </Badge>
  )
}
