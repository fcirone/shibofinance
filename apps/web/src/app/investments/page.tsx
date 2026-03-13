"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import {
  TrendingUp,
  Plus,
  Pencil,
  Building2,
  BarChart3,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { formatAmount } from "@/lib/utils"
import type {
  AssetClass,
  AssetPositionOut,
  InvestmentAccountOut,
} from "@/lib/api"
import {
  useInvestmentAccounts,
  useCreateInvestmentAccount,
  useAssets,
  useCreateAsset,
  useAssetPositions,
  useCreateAssetPosition,
  useUpdateAssetPosition,
  usePortfolioSummary,
} from "@/hooks/useInvestments"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ASSET_CLASS_LABELS: Record<AssetClass, string> = {
  stock: "Stock",
  bond: "Bond",
  etf: "ETF",
  real_estate: "Real Estate",
  crypto: "Crypto",
  cash: "Cash",
  other: "Other",
}

const ASSET_CLASS_OPTIONS: AssetClass[] = [
  "stock", "bond", "etf", "real_estate", "crypto", "cash", "other",
]

// ---------------------------------------------------------------------------
// Add Account Dialog
// ---------------------------------------------------------------------------

const accountSchema = z.object({
  name: z.string().min(1, "Name is required"),
  institution_name: z.string().optional(),
  currency: z.string().min(1).optional(),
})
type AccountForm = z.infer<typeof accountSchema>

function AddAccountDialog() {
  const [open, setOpen] = useState(false)
  const create = useCreateInvestmentAccount()
  const form = useForm<AccountForm>({ resolver: zodResolver(accountSchema) })

  async function onSubmit(data: AccountForm) {
    try {
      await create.mutateAsync({
        name: data.name,
        institution_name: data.institution_name || null,
        currency: data.currency || "BRL",
      })
      toast.success("Investment account created")
      setOpen(false)
      form.reset()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to create account")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Account
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Investment Account</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="acc-name">Name</Label>
            <Input id="acc-name" placeholder="e.g. XP Investimentos" {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="acc-inst">Institution</Label>
            <Input id="acc-inst" placeholder="e.g. XP" {...form.register("institution_name")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="acc-currency">Currency</Label>
            <Input id="acc-currency" placeholder="BRL" defaultValue="BRL" {...form.register("currency")} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>Create</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Add Asset Dialog
// ---------------------------------------------------------------------------

const assetSchema = z.object({
  name: z.string().min(1, "Name is required"),
  symbol: z.string().optional(),
  asset_class: z.enum(["stock", "bond", "etf", "real_estate", "crypto", "cash", "other"] as const),
  currency: z.string().optional(),
})
type AssetForm = z.infer<typeof assetSchema>

function AddAssetDialog() {
  const [open, setOpen] = useState(false)
  const [assetClass, setAssetClass] = useState<AssetClass>("stock")
  const create = useCreateAsset()
  const form = useForm<AssetForm>({
    resolver: zodResolver(assetSchema),
    defaultValues: { asset_class: "stock", currency: "BRL" },
  })

  async function onSubmit(data: AssetForm) {
    try {
      await create.mutateAsync({
        name: data.name,
        symbol: data.symbol || null,
        asset_class: data.asset_class,
        currency: data.currency || "BRL",
      })
      toast.success("Asset created")
      setOpen(false)
      form.reset()
      setAssetClass("stock")
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to create asset")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Asset
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Asset</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="asset-name">Name</Label>
            <Input id="asset-name" placeholder="e.g. Petrobras PN" {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="asset-symbol">Ticker / Symbol</Label>
            <Input id="asset-symbol" placeholder="e.g. PETR4" {...form.register("symbol")} />
          </div>
          <div className="space-y-1.5">
            <Label>Asset Class</Label>
            <Select
              value={assetClass}
              onValueChange={(v) => {
                setAssetClass(v as AssetClass)
                form.setValue("asset_class", v as AssetClass)
              }}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ASSET_CLASS_OPTIONS.map((cls) => (
                  <SelectItem key={cls} value={cls}>{ASSET_CLASS_LABELS[cls]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="asset-currency">Currency</Label>
            <Input id="asset-currency" placeholder="BRL" defaultValue="BRL" {...form.register("currency")} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>Create</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Add Position Dialog
// ---------------------------------------------------------------------------

const positionSchema = z.object({
  investment_account_id: z.string().uuid("Select an account"),
  asset_id: z.string().uuid("Select an asset"),
  quantity: z.coerce.number().positive("Must be positive").optional(),
  average_cost_minor: z.coerce.number().int().min(0).optional(),
  current_value_minor: z.coerce.number().int().min(0).optional(),
  as_of_date: z.string().min(1, "Date is required"),
})
type PositionForm = z.infer<typeof positionSchema>

function AddPositionDialog({
  accounts,
  onSuccess,
}: {
  accounts: InvestmentAccountOut[]
  onSuccess: () => void
}) {
  const [open, setOpen] = useState(false)
  const [accountId, setAccountId] = useState("")
  const [assetId, setAssetId] = useState("")
  const { data: assets } = useAssets()
  const create = useCreateAssetPosition()
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<any>({ resolver: zodResolver(positionSchema) })

  async function onSubmit(data: PositionForm) {
    try {
      await create.mutateAsync({
        investment_account_id: data.investment_account_id,
        asset_id: data.asset_id,
        quantity: data.quantity ?? 0,
        average_cost_minor: data.average_cost_minor ?? null,
        current_value_minor: data.current_value_minor ?? null,
        as_of_date: data.as_of_date,
      })
      toast.success("Position added")
      setOpen(false)
      form.reset()
      setAccountId("")
      setAssetId("")
      onSuccess()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to add position")
    }
  }

  const today = new Date().toISOString().split("T")[0]

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-1.5" />
          Add Position
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Position</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label>Account</Label>
            <Select value={accountId} onValueChange={(v) => { setAccountId(v); form.setValue("investment_account_id", v) }}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Select account" />
              </SelectTrigger>
              <SelectContent>
                {accounts.map((a) => (
                  <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.investment_account_id && (
              <p className="text-xs text-destructive">{form.formState.errors.investment_account_id.message as string}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label>Asset</Label>
            <Select value={assetId} onValueChange={(v) => { setAssetId(v); form.setValue("asset_id", v) }}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Select asset" />
              </SelectTrigger>
              <SelectContent>
                {(assets ?? []).map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.symbol ? `${a.symbol} — ` : ""}{a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.asset_id && (
              <p className="text-xs text-destructive">{form.formState.errors.asset_id.message as string}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="pos-qty">Quantity</Label>
            <Input id="pos-qty" type="number" step="any" placeholder="e.g. 100" {...form.register("quantity")} />
            {form.formState.errors.quantity && (
              <p className="text-xs text-destructive">{form.formState.errors.quantity.message as string}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="pos-avg">Avg Cost (minor)</Label>
              <Input id="pos-avg" type="number" placeholder="e.g. 7500" {...form.register("average_cost_minor")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pos-val">Current Value (minor)</Label>
              <Input id="pos-val" type="number" placeholder="e.g. 8200" {...form.register("current_value_minor")} />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="pos-date">As of Date</Label>
            <Input id="pos-date" type="date" defaultValue={today} {...form.register("as_of_date")} />
            {form.formState.errors.as_of_date && (
              <p className="text-xs text-destructive">{form.formState.errors.as_of_date.message as string}</p>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={form.formState.isSubmitting || create.isPending}>Add</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Update Position Dialog
// ---------------------------------------------------------------------------

function UpdatePositionDialog({ position }: { position: AssetPositionOut }) {
  const [open, setOpen] = useState(false)
  const update = useUpdateAssetPosition()

  const schema = z.object({
    quantity: z.coerce.number().min(0).optional(),
    current_value_minor: z.coerce.number().int().min(0).optional(),
    as_of_date: z.string().optional(),
  })
  type UpdateForm = z.infer<typeof schema>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const form = useForm<any>({
    resolver: zodResolver(schema),
    defaultValues: {
      quantity: position.quantity,
      current_value_minor: position.current_value_minor ?? undefined,
      as_of_date: position.as_of_date,
    },
  })

  async function onSubmit(data: UpdateForm) {
    try {
      await update.mutateAsync({
        id: position.id,
        data: {
          quantity: data.quantity,
          current_value_minor: data.current_value_minor ?? null,
          as_of_date: data.as_of_date ?? null,
        },
      })
      toast.success("Position updated")
      setOpen(false)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to update position")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="icon" variant="ghost" className="h-7 w-7" title="Edit position">
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Update Position — {position.asset_symbol ?? position.asset_name}</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-2">
          <div className="space-y-1.5">
            <Label htmlFor="upd-qty">Quantity</Label>
            <Input id="upd-qty" type="number" step="any" {...form.register("quantity")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="upd-val">Current Value (minor units)</Label>
            <Input id="upd-val" type="number" {...form.register("current_value_minor")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="upd-date">As of Date</Label>
            <Input id="upd-date" type="date" {...form.register("as_of_date")} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={form.formState.isSubmitting || update.isPending}>Save</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ---------------------------------------------------------------------------
// Asset class badge
// ---------------------------------------------------------------------------

const CLASS_COLORS: Record<AssetClass, string> = {
  stock: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  bond: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  etf: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300",
  real_estate: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  crypto: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  cash: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  other: "bg-muted text-muted-foreground",
}

function AssetClassBadge({ cls }: { cls: AssetClass }) {
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${CLASS_COLORS[cls]}`}>
      {ASSET_CLASS_LABELS[cls]}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Positions table for one account
// ---------------------------------------------------------------------------

function AccountPositionsTable({
  account,
  positions,
}: {
  account: InvestmentAccountOut
  positions: AssetPositionOut[]
}) {
  const accountPositions = positions.filter(p => p.investment_account_id === account.id)
  const accountTotal = accountPositions.reduce((s, p) => s + (p.current_value_minor ?? 0), 0)

  return (
    <div className="rounded-lg border border-border overflow-hidden bg-card">
      {/* Account header */}
      <div className="flex items-center justify-between px-4 py-3 bg-muted/40 border-b border-border">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground" />
          <span className="text-[13px] font-semibold">{account.name}</span>
          {account.institution_name && (
            <span className="text-[11px] text-muted-foreground">({account.institution_name})</span>
          )}
        </div>
        <span className="text-[13px] font-mono font-medium">
          {formatAmount(accountTotal, account.currency)}
        </span>
      </div>

      {accountPositions.length === 0 ? (
        <div className="px-4 py-8 text-center text-[13px] text-muted-foreground">
          No positions yet. Add a position to get started.
        </div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="py-2 px-4 text-left text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Asset</th>
              <th className="py-2 px-4 text-left text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Class</th>
              <th className="py-2 px-4 text-right text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Quantity</th>
              <th className="py-2 px-4 text-right text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Avg Cost</th>
              <th className="py-2 px-4 text-right text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Current Value</th>
              <th className="py-2 px-4 text-left text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">As of</th>
              <th className="py-2 px-4" />
            </tr>
          </thead>
          <tbody>
            {accountPositions.map((pos) => (
              <tr key={pos.id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                <td className="py-2.5 px-4">
                  <div className="flex flex-col min-w-0">
                    <span className="text-[13px] font-medium">{pos.asset_symbol ?? pos.asset_name}</span>
                    {pos.asset_symbol && (
                      <span className="text-[11px] text-muted-foreground truncate">{pos.asset_name}</span>
                    )}
                  </div>
                </td>
                <td className="py-2.5 px-4">
                  <AssetClassBadge cls={pos.asset_class} />
                </td>
                <td className="py-2.5 px-4 text-right text-[13px] font-mono">
                  {pos.quantity.toLocaleString()}
                </td>
                <td className="py-2.5 px-4 text-right text-[13px] font-mono text-muted-foreground">
                  {pos.average_cost_minor != null ? formatAmount(pos.average_cost_minor, account.currency) : "—"}
                </td>
                <td className="py-2.5 px-4 text-right text-[13px] font-mono">
                  {pos.current_value_minor != null ? formatAmount(pos.current_value_minor, account.currency) : "—"}
                </td>
                <td className="py-2.5 px-4 text-[12px] text-muted-foreground">
                  {pos.as_of_date}
                </td>
                <td className="py-2.5 px-4">
                  <UpdatePositionDialog position={pos} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Allocation bar
// ---------------------------------------------------------------------------

function AllocationBar({ allocation }: { allocation: { asset_class: AssetClass; pct: number }[] }) {
  const BAR_COLORS: Record<AssetClass, string> = {
    stock: "bg-blue-500",
    bond: "bg-amber-500",
    etf: "bg-violet-500",
    real_estate: "bg-emerald-500",
    crypto: "bg-orange-500",
    cash: "bg-green-500",
    other: "bg-gray-400",
  }

  return (
    <div className="space-y-3">
      <div className="flex h-3 rounded-full overflow-hidden gap-px">
        {allocation.map((item) => (
          <div
            key={item.asset_class}
            className={`${BAR_COLORS[item.asset_class]} transition-all`}
            style={{ width: `${item.pct}%` }}
            title={`${ASSET_CLASS_LABELS[item.asset_class]}: ${item.pct}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {allocation.map((item) => (
          <div key={item.asset_class} className="flex items-center gap-1.5 text-[12px]">
            <div className={`h-2 w-2 rounded-full ${BAR_COLORS[item.asset_class]}`} />
            <span className="text-muted-foreground">{ASSET_CLASS_LABELS[item.asset_class]}</span>
            <span className="font-medium">{item.pct.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function InvestmentsPage() {
  const { data: accounts, isLoading: accountsLoading } = useInvestmentAccounts()
  const { data: positions, isLoading: positionsLoading } = useAssetPositions()
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary()

  const isLoading = accountsLoading || positionsLoading || summaryLoading
  const totalValue = summary?.total_value_minor ?? 0
  const allocation = summary?.allocation ?? []

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Investments</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manual portfolio tracking across all accounts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AddAccountDialog />
          <AddAssetDialog />
          {accounts && accounts.length > 0 && (
            <AddPositionDialog accounts={accounts} onSuccess={() => {}} />
          )}
        </div>
      </div>

      {/* Summary cards */}
      {summaryLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Total Portfolio</p>
            <p className="mt-1 text-2xl font-bold font-mono">{formatAmount(totalValue, "BRL")}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">{accounts?.length ?? 0} account{accounts?.length !== 1 ? "s" : ""}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Positions</p>
            <p className="mt-1 text-2xl font-bold">{positions?.length ?? 0}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">across {summary?.accounts.filter(a => a.total_value_minor > 0).length ?? 0} active accounts</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Asset Classes</p>
            <p className="mt-1 text-2xl font-bold">{allocation.length}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">in portfolio</p>
          </div>
        </div>
      )}

      {/* Allocation chart */}
      {allocation.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-[13px] font-semibold">Allocation by Asset Class</h2>
          </div>
          <AllocationBar allocation={allocation} />
        </div>
      )}

      {/* Empty state — no accounts */}
      {!isLoading && (!accounts || accounts.length === 0) && (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
          <TrendingUp className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">No investment accounts yet</p>
          <p className="text-xs text-muted-foreground/70">
            Click <strong>Add Account</strong> to create your first investment account,
            then add assets and positions to track your portfolio.
          </p>
          <AddAccountDialog />
        </div>
      )}

      {/* Positions by account */}
      {!isLoading && accounts && accounts.length > 0 && (
        <div className="flex flex-col gap-4">
          <h2 className="text-[14px] font-semibold">Positions by Account</h2>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(2)].map((_, i) => <Skeleton key={i} className="h-32 rounded-lg" />)}
            </div>
          ) : (
            accounts.map((account) => (
              <AccountPositionsTable
                key={account.id}
                account={account}
                positions={positions ?? []}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}
