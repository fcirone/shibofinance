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
} from "lucide-react"
import { cn } from "@/lib/utils"

const NAV = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Instruments", href: "/instruments", icon: CreditCard },
  { label: "Import", href: "/import/new", icon: Upload },
  { label: "Import History", href: "/imports", icon: History },
  { label: "Transactions", href: "/transactions", icon: List },
  { label: "Statements", href: "/statements", icon: FileText },
  { label: "Categories", href: "/categories", icon: Tag },
  { label: "Rules", href: "/categories/rules", icon: Sliders },
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
        "flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-200",
        collapsed ? "w-14" : "w-56",
      )}
    >
      {/* Logo / Brand */}
      <div
        className={cn(
          "flex items-center h-14 border-b border-sidebar-border px-3 shrink-0",
          collapsed ? "justify-center" : "gap-2",
        )}
      >
        <span className="text-lg font-bold text-sidebar-primary select-none">
          {collapsed ? "S" : "Shibo Finance"}
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors",
              isActive(href)
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
              collapsed && "justify-center px-2",
            )}
            title={collapsed ? label : undefined}
          aria-label={collapsed ? label : undefined}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!collapsed && <span>{label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
