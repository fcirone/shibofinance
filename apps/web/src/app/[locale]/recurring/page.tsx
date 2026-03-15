"use client"

export const dynamic = 'force-dynamic'

import { useState } from "react"
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { useSearchParams } from "next/navigation"
import { toast } from "sonner"
import { RefreshCw, Check, X, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { formatAmount } from "@/lib/utils"
import type { RecurringPatternOut, RecurringPatternStatus } from "@/lib/api"
import {
  useRecurringPatterns,
  useDetectRecurringPatterns,
  useApprovePattern,
  useIgnorePattern,
} from "@/hooks/usePayables"

// ---------------------------------------------------------------------------
// Pattern card
// ---------------------------------------------------------------------------

function PatternCard({ pattern }: { pattern: RecurringPatternOut }) {
  const t = useTranslations('recurring')
  const approve = useApprovePattern()
  const ignore = useIgnorePattern()

  const CADENCE_LABELS: Record<string, string> = {
    monthly: t('monthly'),
    weekly: t('weekly'),
    yearly: t('yearly'),
    custom: t('custom'),
  }

  const SOURCE_LABELS: Record<string, string> = {
    system: t('autoDetected'),
    manual: t('manual'),
  }

  function statusBadge(status: RecurringPatternStatus) {
    const map: Record<RecurringPatternStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
      suggested: { label: t('suggested'), variant: "secondary" },
      approved:  { label: t('approved'),  variant: "default" },
      ignored:   { label: t('ignored'),   variant: "destructive" },
    }
    const cfg = map[status] ?? map.suggested
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>
  }

  async function handleApprove() {
    try {
      await approve.mutateAsync(pattern.id)
      toast.success(`"${pattern.name}" ${t('approved')}`)
    } catch {
      toast.error(t('approveFailed'))
    }
  }

  async function handleIgnore() {
    try {
      await ignore.mutateAsync(pattern.id)
      toast.success(`"${pattern.name}" ${t('ignored')}`)
    } catch {
      toast.error(t('ignoreFailed'))
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold truncate">{pattern.name}</p>
          <p className="text-[11px] text-muted-foreground font-mono truncate mt-0.5">
            {pattern.normalized_description}
          </p>
        </div>
        <div className="shrink-0">{statusBadge(pattern.status)}</div>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-muted-foreground">
        <span>
          <span className="font-medium text-foreground">{CADENCE_LABELS[pattern.cadence] ?? pattern.cadence}</span>
        </span>
        {pattern.expected_amount_minor != null && (
          <span>
            ~{formatAmount(pattern.expected_amount_minor, "BRL")}
          </span>
        )}
        {pattern.category_name && (
          <span className="text-primary">{pattern.category_name}</span>
        )}
        <span className="ml-auto">{SOURCE_LABELS[pattern.detection_source] ?? pattern.detection_source}</span>
      </div>

      {(pattern.status === "suggested") && (
        <div className="flex gap-2 pt-1 border-t border-border">
          <Button
            size="sm"
            className="flex-1 h-8"
            onClick={handleApprove}
            disabled={approve.isPending || ignore.isPending}
          >
            <Check className="h-3.5 w-3.5 mr-1.5" />
            {t('approve')}
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="flex-1 h-8 text-destructive border-destructive/30 hover:bg-destructive/10"
            onClick={handleIgnore}
            disabled={approve.isPending || ignore.isPending}
          >
            <X className="h-3.5 w-3.5 mr-1.5" />
            {t('ignore')}
          </Button>
        </div>
      )}

      {pattern.status === "approved" && (
        <div className="flex gap-2 pt-1 border-t border-border">
          <Button
            size="sm"
            variant="outline"
            className="h-8 text-destructive border-destructive/30 hover:bg-destructive/10"
            onClick={handleIgnore}
            disabled={ignore.isPending}
          >
            <X className="h-3.5 w-3.5 mr-1.5" />
            {t('ignore')}
          </Button>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function RecurringPage() {
  const t = useTranslations('recurring')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const statusParam = (searchParams.get("status") ?? "all") as "all" | RecurringPatternStatus

  const STATUS_OPTIONS: { value: "all" | RecurringPatternStatus; label: string }[] = [
    { value: "all", label: t('all') },
    { value: "suggested", label: t('suggested') },
    { value: "approved", label: t('approved') },
    { value: "ignored", label: t('ignored') },
  ]

  const filterStatus = statusParam === "all" ? undefined : statusParam
  const { data: patterns, isLoading } = useRecurringPatterns(filterStatus)
  const detect = useDetectRecurringPatterns()

  async function handleDetect() {
    try {
      const res = await detect.mutateAsync()
      if (res.created === 0) {
        toast.info(t('noNewPatterns'))
      } else {
        toast.success(t('foundSuggestions', { count: res.created }))
      }
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : t('detectionFailed'))
    }
  }

  function handleStatusChange(value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value === "all") params.delete("status")
    else params.set("status", value)
    router.push(`${pathname}?${params}` as '/recurring')
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{t('title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {t('subtitle')}
          </p>
        </div>
        <Button
          size="sm"
          onClick={handleDetect}
          disabled={detect.isPending}
        >
          <Search className="h-4 w-4 mr-1.5" />
          {detect.isPending ? t('detecting') : t('runDetection')}
        </Button>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <span className="text-[13px] text-muted-foreground">{t('statusFilter')}</span>
        <Select value={statusParam} onValueChange={handleStatusChange}>
          <SelectTrigger className="h-8 w-36 text-[13px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value} className="text-[13px]">
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {patterns && (
          <span className="text-[12px] text-muted-foreground ml-auto">
            {patterns.length} {t('patterns')}
          </span>
        )}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-36 rounded-lg" />)}
        </div>
      ) : !patterns || patterns.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
          <RefreshCw className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">{t('noPatterns')}</p>
          <p className="text-xs text-muted-foreground/70">
            {t('noPatternsDesc')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {patterns.map((p) => (
            <PatternCard key={p.id} pattern={p} />
          ))}
        </div>
      )}
    </div>
  )
}
