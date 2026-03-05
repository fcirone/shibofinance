"use client"

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useUpdateInstrument } from "@/hooks/useInstruments"
import type { InstrumentOut } from "@/lib/api"

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  metadata_raw: z
    .string()
    .optional()
    .refine(
      (v) => !v || v.trim() === "" || (() => { try { JSON.parse(v); return true } catch { return false } })(),
      { message: "Must be valid JSON" },
    ),
})

type FormData = z.infer<typeof schema>

interface Props {
  instrument: InstrumentOut | null
  onOpenChange: (open: boolean) => void
}

export function EditInstrumentDialog({ instrument, onOpenChange }: Props) {
  const update = useUpdateInstrument()

  const form = useForm<FormData>({ resolver: zodResolver(schema) })
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = form

  useEffect(() => {
    if (instrument) {
      reset({
        name: instrument.name,
        metadata_raw: instrument.metadata_
          ? JSON.stringify(instrument.metadata_, null, 2)
          : "",
      })
    }
  }, [instrument, reset])

  async function onSubmit(data: FormData) {
    if (!instrument) return
    try {
      await update.mutateAsync({
        id: instrument.id,
        data: {
          name: data.name,
          metadata_: data.metadata_raw?.trim()
            ? JSON.parse(data.metadata_raw)
            : null,
        },
      })
      toast.success("Instrument updated")
      onOpenChange(false)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to update instrument")
    }
  }

  return (
    <Dialog open={!!instrument} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Instrument</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-2">
          {/* Name */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Name *</label>
            <input
              {...register("name")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>

          {/* Metadata JSON */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Metadata (JSON)</label>
            <textarea
              {...register("metadata_raw")}
              rows={4}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              placeholder="{}"
            />
            {errors.metadata_raw && (
              <p className="text-xs text-destructive">{errors.metadata_raw.message}</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Save"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
