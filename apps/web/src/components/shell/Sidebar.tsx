"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  CreditCard,
  Upload,
  History,
  List,
  FileText,
  Tag,
  Sliders,
  Target,
  CalendarCheck,
  RefreshCw,
  TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ThemeSelector } from "@/components/shared/ThemeSelector"

const NAV_GROUPS = [
  {
    items: [
      { label: "Dashboard", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    label: "Analyze",
    items: [
      { label: "Transactions", href: "/transactions", icon: List },
      { label: "Statements", href: "/statements", icon: FileText },
      { label: "Planning", href: "/planning", icon: Target },
    ],
  },
  {
    label: "Control",
    items: [
      { label: "Payables", href: "/payables", icon: CalendarCheck },
      { label: "Recurring", href: "/recurring", icon: RefreshCw },
      { label: "Investments", href: "/investments", icon: TrendingUp },
    ],
  },
  {
    label: "Data",
    items: [
      { label: "Instruments", href: "/instruments", icon: CreditCard },
      { label: "Import", href: "/import/new", icon: Upload },
      { label: "History", href: "/imports", icon: History },
    ],
  },
  {
    label: "Manage",
    items: [
      { label: "Categories", href: "/categories", icon: Tag },
      { label: "Rules", href: "/categories/rules", icon: Sliders },
    ],
  },
]

interface SidebarProps {
  collapsed?: boolean
}

export function Sidebar({ collapsed = false }: SidebarProps) {
  const pathname = usePathname()

  function isActive(href: string) {
    if (href === "/") return pathname === "/"
    return pathname.startsWith(href)
  }

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out",
        collapsed ? "w-[60px]" : "w-[220px]",
      )}
    >
      {/* Brand */}
      <div
        className={cn(
          "flex items-center h-14 border-b border-sidebar-border shrink-0 px-3",
          collapsed ? "justify-center" : "gap-3",
        )}
      >
        {/* Hexagon logo mark */}
        <div className="relative flex h-7 w-7 items-center justify-center rounded-lg bg-primary/15 border border-primary/30 shrink-0">
          <svg
            width="13"
            height="13"
            viewBox="0 0 14 14"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M7 1L13 4.5V9.5L7 13L1 9.5V4.5L7 1Z"
              fill="currentColor"
              className="text-primary"
              fillOpacity="0.95"
            />
          </svg>
        </div>

        {!collapsed && (
          <div className="flex flex-col leading-none min-w-0">
            <span className="text-[13px] font-semibold text-sidebar-foreground tracking-tight select-none">
              Shibo
            </span>
            <span
              className="text-[9px] font-medium tracking-[0.15em] uppercase select-none text-sidebar-foreground/40"
            >
              Finance
            </span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 min-h-0">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className={cn(gi > 0 && "mt-1")}>
            {/* Group label — expanded */}
            {group.label && !collapsed && (
              <p className="px-4 pb-1 pt-3 text-[9px] font-semibold uppercase tracking-[0.15em] text-sidebar-foreground/35 select-none">
                {group.label}
              </p>
            )}
            {/* Group divider — collapsed */}
            {group.label && collapsed && (
              <div className="my-2 mx-3 h-px bg-sidebar-border" />
            )}

            {/* Nav items */}
            <div className="px-2 space-y-px">
              {group.items.map(({ label, href, icon: Icon }) => {
                const active = isActive(href)
                return (
                  <div key={href} className="relative">
                    {/* Active left indicator */}
                    {active && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 h-[18px] w-[3px] rounded-r-full bg-primary pointer-events-none z-10" />
                    )}
                    <Link
                      href={href}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md py-[7px] text-[13px] font-medium transition-all duration-150",
                        collapsed ? "justify-center px-2" : "px-2.5",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-foreground/90",
                      )}
                      title={collapsed ? label : undefined}
                      aria-label={collapsed ? label : undefined}
                    >
                      <Icon
                        className={cn(
                          "shrink-0 transition-colors",
                          collapsed ? "h-[18px] w-[18px]" : "h-[15px] w-[15px]",
                          active
                            ? "text-primary"
                            : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground/80",
                        )}
                        aria-hidden="true"
                      />
                      {!collapsed && (
                        <span className="truncate">{label}</span>
                      )}
                    </Link>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Theme selector footer */}
      <div className="shrink-0 border-t border-sidebar-border px-2 py-2">
        <ThemeSelector collapsed={collapsed} />
      </div>
    </aside>
  )
}
