"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"

interface Props {
  page: number
  pageSize: number
  count: number
  basePath: string
}

export function PaginationBar({ page, pageSize, count, basePath }: Props) {
  const router = useRouter()
  const searchParams = useSearchParams()

  const from = (page - 1) * pageSize + 1
  const to = (page - 1) * pageSize + count
  const hasPrev = page > 1
  const hasNext = count === pageSize

  function go(p: number) {
    const params = new URLSearchParams(searchParams.toString())
    params.set("page", String(p))
    router.replace(`${basePath}?${params}`)
  }

  if (!hasPrev && !hasNext) return null

  return (
    <div className="flex items-center justify-between pt-2">
      <Button variant="outline" size="sm" disabled={!hasPrev} onClick={() => go(page - 1)}>
        Previous
      </Button>
      <span className="text-sm text-muted-foreground">
        {count === 0 ? "No results" : `${from}–${to}`}
      </span>
      <Button variant="outline" size="sm" disabled={!hasNext} onClick={() => go(page + 1)}>
        Next
      </Button>
    </div>
  )
}
