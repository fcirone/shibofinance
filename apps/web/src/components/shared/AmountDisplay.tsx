import { formatAmount } from "@/lib/utils"
import { cn } from "@/lib/utils"

interface AmountDisplayProps {
  minor: number
  currency: string
  className?: string
}

export function AmountDisplay({ minor, currency, className }: AmountDisplayProps) {
  return (
    <span
      className={cn(
        "font-mono tabular-nums",
        minor < 0 ? "text-destructive" : "text-foreground",
        className,
      )}
    >
      {formatAmount(minor, currency)}
    </span>
  )
}
