"use client"

import { useState } from "react"
import { useTranslations } from 'next-intl'
import { CreditCard } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { CardSkeleton } from "@/components/shared/LoadingSkeleton"
import { InstrumentCard } from "@/components/instruments/InstrumentCard"
import { CreateInstrumentDialog } from "@/components/instruments/CreateInstrumentDialog"
import { EditInstrumentDialog } from "@/components/instruments/EditInstrumentDialog"
import { useInstruments } from "@/hooks/useInstruments"
import type { InstrumentOut } from "@/lib/api"

export default function InstrumentsPage() {
  const t = useTranslations('instruments')
  const { data: instruments = [], isLoading } = useInstruments()
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<InstrumentOut | null>(null)

  return (
    <>
      <PageHeader
        title={t('title')}
        action={
          <Button onClick={() => setCreateOpen(true)}>
            {t('addInstrument')}
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : instruments.length === 0 ? (
        <EmptyState
          icon={CreditCard}
          title={t('noInstruments')}
          description={t('noInstrumentsDesc')}
          action={{ label: t('addInstrument'), onClick: () => setCreateOpen(true) }}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {instruments.map((inst) => (
            <InstrumentCard
              key={inst.id}
              instrument={inst}
              onEdit={setEditing}
            />
          ))}
        </div>
      )}

      <CreateInstrumentDialog open={createOpen} onOpenChange={setCreateOpen} />
      <EditInstrumentDialog instrument={editing} onOpenChange={(open) => !open && setEditing(null)} />
    </>
  )
}
