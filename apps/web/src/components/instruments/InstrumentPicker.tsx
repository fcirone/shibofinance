"use client"

import { useTranslations } from 'next-intl'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useInstruments } from "@/hooks/useInstruments"
import type { InstrumentType } from "@/lib/api"

const ALL_SENTINEL = "__all__"

interface InstrumentPickerProps {
  value: string | undefined
  onChange: (value: string | undefined) => void
  typeFilter?: InstrumentType
  placeholder?: string
  allowAll?: boolean
  allLabel?: string
}

export function InstrumentPicker({
  value,
  onChange,
  typeFilter,
  placeholder,
  allowAll = false,
  allLabel,
}: InstrumentPickerProps) {
  const t = useTranslations('instruments')
  const tc = useTranslations('common')
  const resolvedPlaceholder = placeholder ?? t('selectInstrument')
  const resolvedAllLabel = allLabel ?? t('allInstruments')
  const { data: instruments = [], isLoading } = useInstruments()

  const filtered = typeFilter
    ? instruments.filter((i) => i.type === typeFilter)
    : instruments

  function handleChange(v: string) {
    if (v === ALL_SENTINEL) onChange(undefined)
    else onChange(v)
  }

  const selectValue = value ?? (allowAll ? ALL_SENTINEL : "")

  return (
    <Select value={selectValue} onValueChange={handleChange} disabled={isLoading}>
      <SelectTrigger>
        <SelectValue placeholder={isLoading ? tc('loading') : resolvedPlaceholder} />
      </SelectTrigger>
      <SelectContent>
        {allowAll && (
          <SelectItem value={ALL_SENTINEL}>{resolvedAllLabel}</SelectItem>
        )}
        {filtered.map((inst) => (
          <SelectItem key={inst.id} value={inst.id}>
            {inst.name}
            <span className="ml-1 text-xs text-muted-foreground">
              ({inst.currency})
            </span>
          </SelectItem>
        ))}
        {!isLoading && filtered.length === 0 && (
          <div className="px-3 py-2 text-sm text-muted-foreground">
            {t('noInstrumentsFound')}
          </div>
        )}
      </SelectContent>
    </Select>
  )
}
