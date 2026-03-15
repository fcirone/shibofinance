"use client"

export const dynamic = 'force-dynamic'

import { useState, useCallback } from "react"
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { useSearchParams } from "next/navigation"
import { FileText } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton"
import { InstrumentPicker } from "@/components/instruments/InstrumentPicker"
import { StatementCard } from "@/components/statements/StatementCard"
import { StatementDetailDrawer } from "@/components/statements/StatementDetailDrawer"
import { useStatements } from "@/hooks/useStatements"
import type { CardStatementOut } from "@/lib/api"

export default function StatementsPage() {
  const t = useTranslations('statements')
  const ti = useTranslations('imports')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const instrumentId = searchParams.get("instrument_id") ?? undefined

  const { data: statements = [], isLoading } = useStatements({ instrument_id: instrumentId })
  const [selected, setSelected] = useState<CardStatementOut | null>(null)

  const setInstrumentFilter = useCallback(
    (id: string | undefined) => {
      const params = new URLSearchParams(searchParams.toString())
      if (id) params.set("instrument_id", id)
      else params.delete("instrument_id")
      router.replace(`${pathname}?${params}` as '/statements')
    },
    [router, pathname, searchParams],
  )

  // Sort newest-first by statement_end
  const sorted = [...statements].sort(
    (a, b) => b.statement_end.localeCompare(a.statement_end),
  )

  return (
    <>
      <PageHeader title={t('title')} />

      {/* Filter bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-64">
          <InstrumentPicker
            value={instrumentId}
            onChange={setInstrumentFilter}
            typeFilter="credit_card"
            allowAll
            allLabel={t('allCreditCards')}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={t('noStatements')}
          description={
            instrumentId
              ? t('noStatementsForCard')
              : t('noStatementsDesc')
          }
          action={{ label: ti('importFile'), onClick: () => router.push("/import/new") }}
        />
      ) : (
        <div className="space-y-3">
          {sorted.map((statement) => (
            <StatementCard
              key={statement.id}
              statement={statement}
              onClick={() => setSelected(statement)}
            />
          ))}
        </div>
      )}

      <StatementDetailDrawer
        statement={selected}
        instrumentId={instrumentId}
        open={!!selected}
        onOpenChange={(open) => !open && setSelected(null)}
      />
    </>
  )
}
