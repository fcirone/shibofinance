"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import {
  ChevronFirst,
  ChevronLast,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"

interface Props {
  page: number
  pageSize: number
  total: number
  basePath: string
}

export function PaginationBar({ page, pageSize, total, basePath }: Props) {
  const tc = useTranslations('common')
  const router = useRouter()
  const searchParams = useSearchParams()
  const [jumpValue, setJumpValue] = useState("")

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, total)
  const hasPrev = page > 1
  const hasNext = page < totalPages

  function go(p: number) {
    const params = new URLSearchParams(searchParams.toString())
    params.set("page", String(p))
    router.replace(`${basePath}?${params}`)
  }

  function handleJump(e: React.FormEvent) {
    e.preventDefault()
    const n = parseInt(jumpValue, 10)
    if (!isNaN(n) && n >= 1 && n <= totalPages) {
      go(n)
      setJumpValue("")
    }
  }

  if (total === 0) return null

  return (
    <div className="flex items-center justify-between gap-4 pt-2 flex-wrap">
      {/* Left: record/page info */}
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {from}–{to} {tc('of')} {total.toLocaleString()} {tc('records')} &middot; {tc('page')} {page} {tc('of')} {totalPages}
      </span>

      {/* Center: nav buttons */}
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={!hasPrev}
          onClick={() => go(1)}
          title={tc('firstPage')}
        >
          <ChevronFirst className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={!hasPrev}
          onClick={() => go(page - 1)}
          title={tc('previousPage')}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={!hasNext}
          onClick={() => go(page + 1)}
          title={tc('nextPage')}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={!hasNext}
          onClick={() => go(totalPages)}
          title={tc('lastPage')}
        >
          <ChevronLast className="h-4 w-4" />
        </Button>
      </div>

      {/* Right: jump to page */}
      {totalPages > 1 && (
        <form onSubmit={handleJump} className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground whitespace-nowrap">{tc('goTo')}</span>
          <input
            type="number"
            min={1}
            max={totalPages}
            value={jumpValue}
            onChange={(e) => setJumpValue(e.target.value)}
            className="h-8 w-16 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder={String(page)}
          />
          <Button type="submit" variant="outline" size="sm" className="h-8">
            {tc('go')}
          </Button>
        </form>
      )}
    </div>
  )
}
