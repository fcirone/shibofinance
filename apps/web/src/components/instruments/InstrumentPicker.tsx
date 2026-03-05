"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useInstruments } from "@/hooks/useInstruments"
import type { InstrumentType } from "@/lib/api"

interface InstrumentPickerProps {
  value: string
  onChange: (value: string) => void
  typeFilter?: InstrumentType
  placeholder?: string
  allowAll?: boolean
}

export function InstrumentPicker({
  value,
  onChange,
  typeFilter,
  placeholder = "Select instrument",
  allowAll = false,
}: InstrumentPickerProps) {
  const { data: instruments = [], isLoading } = useInstruments()

  const filtered = typeFilter
    ? instruments.filter((i) => i.type === typeFilter)
    : instruments

  return (
    <Select value={value} onValueChange={onChange} disabled={isLoading}>
      <SelectTrigger>
        <SelectValue placeholder={isLoading ? "Loading…" : placeholder} />
      </SelectTrigger>
      <SelectContent>
        {allowAll && (
          <SelectItem value="all">All instruments</SelectItem>
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
            No instruments found
          </div>
        )}
      </SelectContent>
    </Select>
  )
}
