"use client"

export const dynamic = 'force-dynamic'

import { useState, useCallback } from "react"
import { useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { useSearchParams } from "next/navigation"
import { Upload, Inbox } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton"
import { InstrumentPicker } from "@/components/instruments/InstrumentPicker"
import { ImportBatchCard } from "@/components/imports/ImportBatchCard"
import { BatchDetailDrawer } from "@/components/imports/BatchDetailDrawer"
import { PaginationBar } from "@/components/shared/PaginationBar"
import { useImports } from "@/hooks/useImports"
import { useInstruments } from "@/hooks/useInstruments"
import type { ImportBatchOut } from "@/lib/api"

const PAGE_SIZE = 50

export default function ImportsPage() {
  const t = useTranslations('imports')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const instrumentId = searchParams.get("instrument_id") ?? undefined
  const page = Number(searchParams.get("page") ?? "1")
  const offset = (page - 1) * PAGE_SIZE

  const { data: importsResult, isLoading } = useImports({
    instrument_id: instrumentId,
    limit: PAGE_SIZE,
    offset,
  })
  const batches = importsResult?.data ?? []
  const importsTotal = importsResult?.total ?? 0
  const { data: instruments = [] } = useInstruments()

  const [selected, setSelected] = useState<ImportBatchOut | null>(null)

  const setInstrumentFilter = useCallback(
    (id: string | undefined) => {
      const params = new URLSearchParams(searchParams.toString())
      if (id) params.set("instrument_id", id)
      else params.delete("instrument_id")
      params.delete("page")
      router.replace(`${pathname}?${params}` as '/imports')
    },
    [router, pathname, searchParams],
  )

  const selectedInstrument = instruments.find((i) => i.id === selected?.instrument_id)

  return (
    <>
      <PageHeader
        title={t('history')}
        action={
          <Button onClick={() => router.push("/import/new")}>
            <Upload className="h-4 w-4 mr-2" />
            {t('importFile')}
          </Button>
        }
      />

      {/* Filter bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-64">
          <InstrumentPicker
            value={instrumentId}
            onChange={setInstrumentFilter}
            allowAll
            allLabel={t('allInstruments')}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <LoadingSkeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : batches.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title={t('noImports')}
          description={
            instrumentId
              ? t('noImportsForInstrument')
              : t('noImportsDesc')
          }
          action={{ label: t('importFile'), onClick: () => router.push("/import/new") }}
        />
      ) : (
        <div className="space-y-3">
          {batches.map((batch) => {
            const inst = instruments.find((i) => i.id === batch.instrument_id)
            return (
              <ImportBatchCard
                key={batch.id}
                batch={batch}
                instrument={inst}
                onClick={() => setSelected(batch)}
              />
            )
          })}

          <PaginationBar
            page={page}
            pageSize={PAGE_SIZE}
            total={importsTotal}
            basePath="/imports"
          />
        </div>
      )}

      <BatchDetailDrawer
        batch={selected}
        instrument={selectedInstrument}
        open={!!selected}
        onOpenChange={(open) => !open && setSelected(null)}
      />
    </>
  )
}
