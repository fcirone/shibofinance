"use client"

import { useLocale, useTranslations } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { PanelLeftClose, PanelLeftOpen, Menu, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Sidebar } from "./Sidebar"

const LOCALES = [
  { value: "pt", label: "Português" },
  { value: "en", label: "English" },
  { value: "es", label: "Español" },
] as const

interface TopbarProps {
  onToggleCollapse?: () => void
  collapsed?: boolean
}

export function Topbar({ onToggleCollapse, collapsed }: TopbarProps) {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const tc = useTranslations('common')

  function switchLocale(nextLocale: string) {
    router.replace(pathname as '/', { locale: nextLocale })
  }

  return (
    <header className="flex items-center h-14 border-b border-border bg-background/80 backdrop-blur-md px-4 gap-3 shrink-0">
      {/* Desktop collapse toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="hidden lg:flex h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-secondary/80"
        onClick={onToggleCollapse}
        aria-label={collapsed ? tc('expandSidebar') : tc('collapseSidebar')}
      >
        {collapsed ? (
          <PanelLeftOpen className="h-[15px] w-[15px]" />
        ) : (
          <PanelLeftClose className="h-[15px] w-[15px]" />
        )}
      </Button>

      {/* Mobile hamburger */}
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label={tc('openNavigation')}
          >
            <Menu className="h-[15px] w-[15px]" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-[220px]">
          <SheetHeader className="sr-only">
            <SheetTitle>{tc('navigation')}</SheetTitle>
          </SheetHeader>
          <Sidebar />
        </SheetContent>
      </Sheet>

      <div className="flex-1" />

      {/* Language switcher */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-muted-foreground hover:text-foreground px-2"
            aria-label={tc('switchLanguage')}
          >
            <Globe className="h-[14px] w-[14px]" />
            <span className="text-[12px] font-medium uppercase">{locale}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-[130px]">
          {LOCALES.map(({ value, label }) => (
            <DropdownMenuItem
              key={value}
              onClick={() => switchLocale(value)}
              className={value === locale ? "font-semibold text-primary" : ""}
            >
              {label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}
