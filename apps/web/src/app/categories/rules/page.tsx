"use client"

import { useState } from "react"
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
// Labels
// ---------------------------------------------------------------------------

const matchFieldLabels: Record<MatchField, string> = {
  description_raw: "Description (raw)",
  description_norm: "Description (normalized)",
  merchant_raw: "Merchant",
  amount_minor: "Amount",
}

const matchOperatorLabels: Record<MatchOperator, string> = {
  contains: "contains",
  equals: "equals",
  regex: "matches regex",
  gte: "≥",
  lte: "≤",
}

const targetTypeLabels: Record<RuleTargetType, string> = {
  bank_transaction: "Bank",
  card_transaction: "Card",
  both: "Both",
}

// Operators allowed per match field
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

  // If current operator not allowed for current field, reset to first allowed
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
        toast.success("Rule updated")
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
        toast.success("Rule created")
      }
      reset()
      onClose()
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to save rule")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose() } }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{rule ? "Edit Rule" : "New Rule"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
          {/* Category */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Category</label>
            <select
              {...register("category_id")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select a category…</option>
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
            <label className="text-sm font-medium">Match Field</label>
            <select
              value={watchedField}
              onChange={(e) => handleFieldChange(e.target.value as MatchField)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {(Object.keys(matchFieldLabels) as MatchField[]).map((f) => (
                <option key={f} value={f}>
                  {matchFieldLabels[f]}
                </option>
              ))}
            </select>
          </div>

          {/* Operator */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Operator</label>
            <select
              {...register("match_operator")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {allowedOperators.map((op) => (
                <option key={op} value={op}>
                  {matchOperatorLabels[op]}
                </option>
              ))}
            </select>
            {errors.match_operator && (
              <p className="text-xs text-destructive">{errors.match_operator.message}</p>
            )}
          </div>

          {/* Match value */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Match Value</label>
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
            <label className="text-sm font-medium">Applies To</label>
            <select
              {...register("target_type")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {(Object.keys(targetTypeLabels) as RuleTargetType[]).map((t) => (
                <option key={t} value={t}>
                  {targetTypeLabels[t]}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div className="space-y-1">
            <label className="text-sm font-medium">Priority</label>
            <input
              type="number"
              {...register("priority", { valueAsNumber: true })}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              min={0}
            />
            <p className="text-xs text-muted-foreground">Lower number = higher priority</p>
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
              Enabled
            </label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { reset(); onClose() }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {rule ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Dry-run preview modal (Task 24.13)
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
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Apply Rules Preview</DialogTitle>
          <DialogDescription>
            {dryRunResult
              ? `This will categorize ${dryRunResult.would_categorize} transaction${dryRunResult.would_categorize !== 1 ? "s" : ""}:`
              : "Calculating…"}
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
          <p className="text-sm text-muted-foreground">No transactions would be categorized.</p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isApplying}>
            Cancel
          </Button>
          <Button
            onClick={onApply}
            disabled={isApplying || !dryRunResult || dryRunResult.would_categorize === 0}
          >
            {isApplying && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Apply
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
    if (!confirm(`Delete this rule for "${rule.category_name}"?`)) return
    try {
      await deleteMutation.mutateAsync(rule.id)
      toast.success("Rule deleted")
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to delete rule")
    }
  }

  async function handleApplyRulesClick() {
    setDryRunResult(null)
    setPreviewOpen(true)
    try {
      const result = await dryRunMutation.mutateAsync()
      setDryRunResult(result)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to preview rules")
      setPreviewOpen(false)
    }
  }

  async function handleConfirmApply() {
    try {
      const result = await applyMutation.mutateAsync()
      toast.success(`Applied to ${result.applied} transaction${result.applied !== 1 ? "s" : ""}`)
      setPreviewOpen(false)
      setDryRunResult(null)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to apply rules")
    }
  }

  return (
    <>
      <PageHeader
        title="Category Rules"
        action={
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleApplyRulesClick}
              disabled={dryRunMutation.isPending || rules.length === 0}
            >
              <Play className="h-4 w-4 mr-1.5" />
              Apply Rules
            </Button>
            <Button size="sm" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-1.5" />
              New Rule
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </div>
      ) : rules.length === 0 ? (
        <EmptyState
          icon={Sliders}
          title="No rules yet"
          description="Create rules to automatically categorize transactions."
          action={{ label: "New Rule", onClick: openCreate }}
        />
      ) : (
        <div className="rounded-lg border overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">Match Field</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">Operator</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">Match Value</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">Category</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">Target</th>
                <th className="px-4 py-2.5 text-right font-medium text-muted-foreground whitespace-nowrap">Priority</th>
                <th className="px-4 py-2.5 text-center font-medium text-muted-foreground">Enabled</th>
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
                    {matchFieldLabels[rule.match_field] ?? rule.match_field}
                  </td>
                  <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground">
                    {matchOperatorLabels[rule.match_operator] ?? rule.match_operator}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs max-w-[200px] truncate" title={rule.match_value}>
                    {rule.match_value}
                  </td>
                  <td className="px-4 py-2.5 font-medium">{rule.category_name}</td>
                  <td className="px-4 py-2.5">
                    <span className="inline-flex rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                      {targetTypeLabels[rule.target_type] ?? rule.target_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{rule.priority}</td>
                  <td className="px-4 py-2.5 text-center">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${rule.enabled ? "bg-green-500" : "bg-muted-foreground/30"}`}
                      aria-label={rule.enabled ? "Enabled" : "Disabled"}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => openEdit(rule)}
                        aria-label="Edit rule"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(rule)}
                        aria-label="Delete rule"
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
