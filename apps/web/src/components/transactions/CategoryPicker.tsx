"use client"

import { useState } from "react"
import { Check, ChevronsUpDown, Loader2, Tag } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useCategories } from "@/hooks/useCategories"
import { categorize, type TargetType } from "@/lib/api"

// Re-export TargetType so callers can import from here
export type { TargetType }

interface Props {
  targetType: TargetType
  targetId: string
  categoryId?: string | null
  categoryName?: string | null
  onSaved?: () => void
}

export function CategoryPicker({
  targetType,
  targetId,
  categoryId,
  categoryName,
  onSaved,
}: Props) {
  const [open, setOpen] = useState(false)
  const { data: categories = [] } = useCategories()
  const qc = useQueryClient()

  const { mutate, isPending } = useMutation({
    mutationFn: (catId: string) =>
      categorize({ target_type: targetType, target_id: targetId, category_id: catId, source: "manual" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bank-transactions"] })
      qc.invalidateQueries({ queryKey: ["card-transactions"] })
      setOpen(false)
      onSaved?.()
    },
    onError: (err: Error) => toast.error(err.message),
  })

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-7 gap-1 px-2 text-xs font-normal",
            !categoryId && "text-muted-foreground",
          )}
          aria-label="Set category"
        >
          {isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Tag className="h-3 w-3 shrink-0" aria-hidden />
          )}
          <span className="max-w-[120px] truncate">
            {categoryName ?? "Uncategorized"}
          </span>
          <ChevronsUpDown className="h-3 w-3 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-52 p-1" align="start">
        <div className="max-h-64 overflow-y-auto space-y-0.5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => mutate(cat.id)}
              className={cn(
                "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent transition-colors text-left",
                cat.id === categoryId && "bg-accent font-medium",
              )}
            >
              <Check
                className={cn(
                  "h-3.5 w-3.5 shrink-0",
                  cat.id === categoryId ? "opacity-100" : "opacity-0",
                )}
              />
              {cat.name}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
