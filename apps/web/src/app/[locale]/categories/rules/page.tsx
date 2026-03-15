"use client"

import { useState } from "react"
import { useTranslations } from 'next-intl'
import { Loader2, Plus, Pencil, Trash2, Play, Sliders } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  useCategoryRules,
  useCreateCategoryRule,
  useUpdateCategoryRule,
  useDeleteCategoryRule,
  useApplyRules,
  useDryRunRules,
} from "@/hooks/useCategoryRules"
import { useCategories } from "@/hooks/useCategories"
import type {
  CategoryRuleOut,
  CategoryRuleCreate,
  CategoryRuleUpdate,
  MatchField,
  MatchOperator,
  RuleTargetType,
  DryRunResult,
} from "@/lib/api"

// ---------------------------------------------------------------------------
// Operators allowed per match field
// ---------------------------------------------------------------------------

const textOperators: MatchOperator[] = ["contains", "equals", "regex"]
const numericOperators: MatchOperator[] = ["gte", "lte", "equals"]

function getAllowedOperators(field: MatchField): MatchOperator[] {
  if (field === "amount_minor") return numericOperators
  return textOperators
}

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const schema = z.object({
  category_id: z.string().min(1, "Category is required"),
  match_field: z.enum(["description_raw", "description_norm", "merchant_raw", "amount_minor"]),
  match_operator: z.enum(["contains", "equals", "regex", "gte", "lte"]),
  match_value: z.string().min(1, "Match value is required"),
  target_type: z.enum(["bank_transaction", "card_transaction", "both"]),
  priority: z.number().int().min(0),
  enabled: z.boolean(),
})

type FormData = z.infer<typeof schema>

// ---------------------------------------------------------------------------
// Create / Edit dialog
// ---------------------------------------------------------------------------

function RuleDialog({
  open,
  rule,
  onClose,
}: {
  open: boolean
  rule?: CategoryRuleOut
  onClose: () => void
}) {
  const t = useTranslations('categoryRules')
  const tc = useTranslations('common')
  const { data: categories = [] } = useCategories()
  const createMutation = useCreateCategoryRule()
  const updateMutation = useUpdateCategoryRule()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: rule
      ? {
          category_id: rule.category_id,
          match_field: rule.match_field,
          match_operator: rule.match_operator,
          match_value: rule.match_value,
          target_type: rule.target_type,
          priority: rule.priority,
          enabled: rule.enabled,
        }
      : {
          category_id: "",
          match_field: "description_raw",
          match_operator: "contains",
          match_value: "",
          target_type: "both",
          priority: 100,
          enabled: true,
        },
  })

  const watchedField = watch("match_field")
  const watchedOperator = watch("match_operator")
  const watchedEnabled = watch("enabled")
  const allowedOperators = getAllowedOperators(watchedField)

  function handleFieldChange(field: MatchField) {
    setValue("match_field", field)
    const allowed = getAllowedOperators(field)
    if (!allowed.includes(watchedOperator)) {
      setValue("match_operator", allowed[0])
    }
  }

  async function onSubmit(data: FormData) {
    try {
      if (rule) {
        const update: CategoryRuleUpdate = {
          category_id: data.category_id,
          match_field: data.match_field,
          match_operator: data.match_operator,
          match_value: data.match_value,
          target_type: data.target_type,
          priority: data.priority,
          enabled: data.enabled,
        }
        await updateMutation.mutateAsync({ id: rule.id, data: update })
        toast.success(t('ruleUpdated'))
      } else {
        const create: CategoryRuleCreate = {
          category_id: data.category_id,
          match_field: data.match_field,
          match_operator: data.match_operator,
          match_value: data.match_value,
          target_type: data.target_type,
          priority: data.priority,
          enabled: data.enabled,
        }
        await createMutation.mutateAsync(create)
        toast.success(t('ruleCreated'))
      }
      reset()
      onClose()
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t('saveFailed'))
    }
  }

  const matchFieldOptions: MatchField[] = ["description_raw", "description_norm", "merchant_raw", "amount_minor"]
  const targetTypeOptions: RuleTargetType[] = ["bank_transaction", "card_transaction", "both"]

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose() } }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{rule ? t('editRule') : t('newRule')}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
          {/* Category */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('category')}</label>
            <select
              {...register("category_id")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">{t('selectCategory')}</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
            {errors.category_id && (
              <p className="text-xs text-destructive">{errors.category_id.message}</p>
            )}
          </div>

          {/* Match field */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('matchField')}</label>
            <select
              value={watchedField}
              onChange={(e) => handleFieldChange(e.target.value as MatchField)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {matchFieldOptions.map((f) => (
                <option key={f} value={f}>
                  {t(`field_${f}` as Parameters<typeof t>[0])}
                </option>
              ))}
            </select>
          </div>

          {/* Operator */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('matchOperator')}</label>
            <select
              {...register("match_operator")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {allowedOperators.map((op) => (
                <option key={op} value={op}>
                  {t(`op_${op}` as Parameters<typeof t>[0])}
                </option>
              ))}
            </select>
            {errors.match_operator && (
              <p className="text-xs text-destructive">{errors.match_operator.message}</p>
            )}
          </div>

          {/* Match value */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('matchValue')}</label>
            <input
              {...register("match_value")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={watchedField === "amount_minor" ? "e.g. 5000 (in minor units)" : "e.g. UBER"}
            />
            {errors.match_value && (
              <p className="text-xs text-destructive">{errors.match_value.message}</p>
            )}
          </div>

          {/* Target type */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('appliesTo')}</label>
            <select
              {...register("target_type")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {targetTypeOptions.map((tt) => (
                <option key={tt} value={tt}>
                  {t(`target_${tt}` as Parameters<typeof t>[0])}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div className="space-y-1">
            <label className="text-sm font-medium">{t('priority')}</label>
            <input
              type="number"
              {...register("priority", { valueAsNumber: true })}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              min={0}
            />
            <p className="text-xs text-muted-foreground">{t('priorityHint')}</p>
            {errors.priority && (
              <p className="text-xs text-destructive">{errors.priority.message}</p>
            )}
          </div>

          {/* Enabled */}
          <div className="flex items-center gap-2">
            <Checkbox
              id="enabled"
              checked={watchedEnabled}
              onCheckedChange={(v) => setValue("enabled", v === true)}
            />
            <label htmlFor="enabled" className="text-sm font-medium cursor-pointer">
              {t('enabled')}
            </label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { reset(); onClose() }}>
              {tc('cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {rule ? tc('save') : tc('create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Dry-run preview modal
// ---------------------------------------------------------------------------

function ApplyPreviewModal({
  open,
  dryRunResult,
  isApplying,
  onApply,
  onClose,
}: {
  open: boolean
  dryRunResult: DryRunResult | null
  isApplying: boolean
  onApply: () => void
  onClose: () => void
}) {
  const t = useTranslations('categoryRules')
  const tc = useTranslations('common')

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{t('previewTitle')}</DialogTitle>
          <DialogDescription>
            {dryRunResult
              ? t('previewDesc', { count: dryRunResult.would_categorize })
              : t('previewCalculating')}
          </DialogDescription>
        </DialogHeader>
        {dryRunResult && dryRunResult.by_category.length > 0 && (
          <ul className="space-y-1 text-sm max-h-60 overflow-y-auto">
            {dryRunResult.by_category.map((item) => (
              <li key={item.category_name} className="flex justify-between items-center py-1 border-b last:border-0">
                <span>{item.category_name}</span>
                <Badge variant="secondary" className="font-mono">
                  {item.count}
                </Badge>
              </li>
            ))}
          </ul>
        )}
        {dryRunResult && dryRunResult.by_category.length === 0 && (
          <p className="text-sm text-muted-foreground">{t('previewNone')}</p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isApplying}>
            {tc('cancel')}
          </Button>
          <Button
            onClick={onApply}
            disabled={isApplying || !dryRunResult || dryRunResult.would_categorize === 0}
          >
            {isApplying && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t('apply')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CategoryRulesPage() {
  const t = useTranslations('categoryRules')
  const { data: rules = [], isLoading } = useCategoryRules()
  const deleteMutation = useDeleteCategoryRule()
  const dryRunMutation = useDryRunRules()
  const applyMutation = useApplyRules()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<CategoryRuleOut | undefined>(undefined)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null)

  function openCreate() {
    setEditing(undefined)
    setDialogOpen(true)
  }

  function openEdit(rule: CategoryRuleOut) {
    setEditing(rule)
    setDialogOpen(true)
  }

  async function handleDelete(rule: CategoryRuleOut) {
    if (!confirm(t('deleteRuleConfirm', { name: rule.category_name }))) return
    try {
      await deleteMutation.mutateAsync(rule.id)
      toast.success(t('ruleDeleted'))
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t('deleteFailed'))
    }
  }

  async function handleApplyRulesClick() {
    setDryRunResult(null)
    setPreviewOpen(true)
    try {
      const result = await dryRunMutation.mutateAsync()
      setDryRunResult(result)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t('previewFailed'))
      setPreviewOpen(false)
    }
  }

  async function handleConfirmApply() {
    try {
      const result = await applyMutation.mutateAsync()
      toast.success(t('applied', { count: result.applied }))
      setPreviewOpen(false)
      setDryRunResult(null)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t('applyFailed'))
    }
  }

  return (
    <>
      <PageHeader
        title={t('title')}
        action={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleApplyRulesClick}
              disabled={dryRunMutation.isPending || rules.length === 0}
            >
              <Play className="h-4 w-4 mr-1.5" />
              {t('applyRules')}
            </Button>
            <Button size="sm" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-1.5" />
              {t('newRule')}
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          {t('loadingRules')}
        </div>
      ) : rules.length === 0 ? (
        <EmptyState
          icon={Sliders}
          title={t('noRules')}
          description={t('noRulesDesc')}
          action={{ label: t('newRule'), onClick: openCreate }}
        />
      ) : (
        <div className="rounded-lg border overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">{t('matchField')}</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">{t('matchOperator')}</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('matchValue')}</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">{t('category')}</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">{t('target')}</th>
                <th className="px-4 py-2.5 text-right font-medium text-muted-foreground whitespace-nowrap">{t('priority')}</th>
                <th className="px-4 py-2.5 text-center font-medium text-muted-foreground">{t('enabled')}</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr
                  key={rule.id}
                  className="border-b last:border-0 hover:bg-muted/20 transition-colors"
                >
                  <td className="px-4 py-2.5 whitespace-nowrap">
                    {t(`field_${rule.match_field}` as Parameters<typeof t>[0])}
                  </td>
                  <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground">
                    {t(`op_${rule.match_operator}` as Parameters<typeof t>[0])}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs max-w-[200px] truncate" title={rule.match_value}>
                    {rule.match_value}
                  </td>
                  <td className="px-4 py-2.5 font-medium">{rule.category_name}</td>
                  <td className="px-4 py-2.5">
                    <span className="inline-flex rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                      {t(`target_${rule.target_type}` as Parameters<typeof t>[0])}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{rule.priority}</td>
                  <td className="px-4 py-2.5 text-center">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${rule.enabled ? "bg-green-500" : "bg-muted-foreground/30"}`}
                      aria-label={rule.enabled ? t('enabled') : t('disabled')}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => openEdit(rule)}
                        aria-label={t('editRule')}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(rule)}
                        aria-label={t('deleteRule')}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <RuleDialog
        open={dialogOpen}
        rule={editing}
        onClose={() => setDialogOpen(false)}
      />

      <ApplyPreviewModal
        open={previewOpen}
        dryRunResult={dryRunResult}
        isApplying={applyMutation.isPending}
        onApply={handleConfirmApply}
        onClose={() => { setPreviewOpen(false); setDryRunResult(null) }}
      />
    </>
  )
}
