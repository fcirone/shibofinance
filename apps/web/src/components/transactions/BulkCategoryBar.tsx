"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Check, Loader2, Tag, X } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { useCategories } from "@/hooks/useCategories"
import { bulkCategorize, type TargetType } from "@/lib/api"

interface Props {
  selectedIds: Set<string>
  targetType: TargetType
  onClear: () => void
}

export function BulkCategoryBar({ selectedIds, targetType, onClear }: Props) {
  const t = useTranslations('transactions')
  const [open, setOpen] = useState(false)
  const { data: categories = [] } = useCategories()
  const qc = useQueryClient()
  const count = selectedIds.size

  const { mutate, isPending } = useMutation({
    mutationFn: (categoryId: string) =>
      bulkCategorize({
        items: Array.from(selectedIds).map((id) => ({
          target_type: targetType,
          target_id: id,
          category_id: categoryId,
          source: "manual",
        })),
      }),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["bank-transactions"] })
      qc.invalidateQueries({ queryKey: ["card-transactions"] })
      toast.success(t('categorized', { count: result.updated + result.created }))
      onClear()
      setOpen(false)
    },
    onError: (err: Error) => toast.error(err.message),
  })

  if (count === 0) return null

  return (
    <div className="sticky top-0 z-10 flex items-center gap-3 rounded-lg border bg-background px-4 py-2.5 shadow-sm">
      <span className="text-sm font-medium">
        {count} {t('selected')}
      </span>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button size="sm" variant="default" disabled={isPending}>
            {isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Tag className="h-3.5 w-3.5" />
            )}
            {t('categorize')}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-52 p-1" align="start">
          <div className="max-h-64 overflow-y-auto space-y-0.5">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => mutate(cat.id)}
                disabled={isPending}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent transition-colors text-left disabled:opacity-50",
                )}
              >
                <Check className="h-3.5 w-3.5 shrink-0 opacity-0" />
                {cat.name}
              </button>
            ))}
          </div>
        </PopoverContent>
      </Popover>

      <Button
        size="sm"
        variant="ghost"
        onClick={onClear}
        disabled={isPending}
        aria-label={t('clearSelection')}
      >
        <X className="h-3.5 w-3.5" />
        {t('clearSelection')}
      </Button>
    </div>
  )
}
