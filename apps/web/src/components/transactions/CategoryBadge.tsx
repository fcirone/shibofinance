"use client"

import { Tag } from "lucide-react"
import { cn } from "@/lib/utils"
import type { CategoryKind } from "@/lib/api"

interface Props {
  name: string
  kind?: CategoryKind
  className?: string
}

const kindColor: Record<CategoryKind, string> = {
  expense: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  income: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  transfer: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
}

export function CategoryBadge({ name, kind, className }: Props) {
  const colorClass = kind ? kindColor[kind] : "bg-muted text-muted-foreground"
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        colorClass,
        className,
      )}
    >
      <Tag className="h-3 w-3 shrink-0" aria-hidden />
      {name}
    </span>
  )
}
