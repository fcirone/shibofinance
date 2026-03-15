"use client"

import { useTranslations } from 'next-intl'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useCreateInstrument } from "@/hooks/useInstruments"

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  type: z.enum(["bank_account", "credit_card"]),
  source: z.enum(["santander_br", "xp_br", "bbva_uy"]),
  currency: z.enum(["BRL", "USD", "UYU"]),
  source_instrument_id: z.string().optional(),
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
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateInstrumentDialog({ open, onOpenChange }: Props) {
  const t = useTranslations('instruments')
  const tc = useTranslations('common')
  const create = useCreateInstrument()

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      source_instrument_id: "",
      metadata_raw: "",
    },
  })

  async function onSubmit(data: FormData) {
    try {
      await create.mutateAsync({
        name: data.name,
        type: data.type,
        source: data.source,
        currency: data.currency,
        source_instrument_id: data.source_instrument_id ?? "",
        metadata_: data.metadata_raw?.trim()
          ? JSON.parse(data.metadata_raw)
          : null,
      })
      toast.success(t('created'))
      form.reset()
      onOpenChange(false)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t('createFailed'))
    }
  }

  const { register, handleSubmit, setValue, watch, formState: { errors, isSubmitting } } = form

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t('addInstrument')}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-2">
          {/* Name */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('nameLabel')} *</label>
            <input
              {...register("name")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('namePlaceholder')}
            />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>

          {/* Type */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('typeLabel')} *</label>
            <Select onValueChange={(v) => setValue("type", v as FormData["type"])}>
              <SelectTrigger>
                <SelectValue placeholder={t('selectType')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bank_account">{t('bankAccount')}</SelectItem>
                <SelectItem value="credit_card">{t('creditCard')}</SelectItem>
              </SelectContent>
            </Select>
            {errors.type && <p className="text-xs text-destructive">{errors.type.message}</p>}
          </div>

          {/* Source */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('sourceLabel')} *</label>
            <Select onValueChange={(v) => setValue("source", v as FormData["source"])}>
              <SelectTrigger>
                <SelectValue placeholder={t('selectSource')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="santander_br">Santander BR</SelectItem>
                <SelectItem value="xp_br">XP BR</SelectItem>
                <SelectItem value="bbva_uy">BBVA UY</SelectItem>
              </SelectContent>
            </Select>
            {errors.source && <p className="text-xs text-destructive">{errors.source.message}</p>}
          </div>

          {/* Currency */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('currencyLabel')} *</label>
            <Select onValueChange={(v) => setValue("currency", v as FormData["currency"])}>
              <SelectTrigger>
                <SelectValue placeholder={t('selectCurrency')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BRL">BRL — Brazilian Real</SelectItem>
                <SelectItem value="USD">USD — US Dollar</SelectItem>
                <SelectItem value="UYU">UYU — Uruguayan Peso</SelectItem>
              </SelectContent>
            </Select>
            {errors.currency && <p className="text-xs text-destructive">{errors.currency.message}</p>}
          </div>

          {/* Source instrument ID */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('sourceIdLabel')}</label>
            <input
              {...register("source_instrument_id")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('sourceIdPlaceholder')}
            />
          </div>

          {/* Metadata JSON */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('metadataLabel')}</label>
            <textarea
              {...register("metadata_raw")}
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              placeholder='{"last4": "1234"}'
            />
            {errors.metadata_raw && (
              <p className="text-xs text-destructive">{errors.metadata_raw.message}</p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {tc('cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? tc('creating') : tc('create')}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
