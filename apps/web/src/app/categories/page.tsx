"use client"

import { useState } from "react"
import { Loader2, Plus, Pencil, Trash2, Tag } from "lucide-react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  useCategories,
  useCreateCategory,
  useDeleteCategory,
  useUpdateCategory,
} from "@/hooks/useCategories"
import type { CategoryOut } from "@/lib/api"

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  kind: z.enum(["expense", "income", "transfer"]),
})
type FormData = z.infer<typeof schema>

// ---------------------------------------------------------------------------
// Create / Edit dialog
// ---------------------------------------------------------------------------

function CategoryDialog({
  open,
  category,
  onClose,
}: {
  open: boolean
  category?: CategoryOut
  onClose: () => void
}) {
  const createMutation = useCreateCategory()
  const updateMutation = useUpdateCategory()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: category
      ? { name: category.name, kind: category.kind }
      : { name: "", kind: "expense" },
  })

  async function onSubmit(data: FormData) {
    try {
      if (category) {
        await updateMutation.mutateAsync({ id: category.id, data })
        toast.success("Category updated")
      } else {
        await createMutation.mutateAsync(data)
        toast.success("Category created")
      }
      reset()
      onClose()
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to save category")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose() } }}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{category ? "Edit Category" : "New Category"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1">
            <label className="text-sm font-medium">Name</label>
            <input
              {...register("name")}
              autoFocus
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="e.g. Food & Dining"
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Kind</label>
            <select
              {...register("kind")}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => { reset(); onClose() }}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {category ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Kind badge
// ---------------------------------------------------------------------------

const kindLabel: Record<string, string> = {
  expense: "Expense",
  income: "Income",
  transfer: "Transfer",
}

const kindColor: Record<string, string> = {
  expense: "bg-orange-100 text-orange-700",
  income: "bg-green-100 text-green-700",
  transfer: "bg-blue-100 text-blue-700",
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CategoriesPage() {
  const { data: categories = [], isLoading } = useCategories()
  const deleteMutation = useDeleteCategory()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<CategoryOut | undefined>(undefined)

  function openCreate() {
    setEditing(undefined)
    setDialogOpen(true)
  }

  function openEdit(cat: CategoryOut) {
    setEditing(cat)
    setDialogOpen(true)
  }

  async function handleDelete(cat: CategoryOut) {
    if (!confirm(`Delete "${cat.name}"?`)) return
    try {
      await deleteMutation.mutateAsync(cat.id)
      toast.success("Category deleted")
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to delete category")
    }
  }

  return (
    <>
      <PageHeader
        title="Categories"
        action={
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1.5" />
            New Category
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </div>
      ) : categories.length === 0 ? (
        <EmptyState
          icon={Tag}
          title="No categories yet"
          description="Create categories to organize your transactions."
          action={{ label: "New Category", onClick: openCreate }}
        />
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-2.5 text-left font-medium text-muted-foreground">Kind</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-2.5 font-medium">{cat.name}</td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${kindColor[cat.kind] ?? ""}`}>
                      {kindLabel[cat.kind] ?? cat.kind}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => openEdit(cat)}
                        aria-label={`Edit ${cat.name}`}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(cat)}
                        aria-label={`Delete ${cat.name}`}
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

      <CategoryDialog
        open={dialogOpen}
        category={editing}
        onClose={() => setDialogOpen(false)}
      />
    </>
  )
}
