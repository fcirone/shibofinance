"use client"

import { PanelLeftClose, PanelLeftOpen, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Sidebar } from "./Sidebar"

interface TopbarProps {
  onToggleCollapse?: () => void
  collapsed?: boolean
}

export function Topbar({ onToggleCollapse, collapsed }: TopbarProps) {
  return (
    <header className="flex items-center h-14 border-b border-border bg-background/80 backdrop-blur-md px-4 gap-3 shrink-0">
      {/* Desktop collapse toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="hidden lg:flex h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-secondary/80"
        onClick={onToggleCollapse}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
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
            aria-label="Open navigation"
          >
            <Menu className="h-[15px] w-[15px]" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-[220px]">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <Sidebar />
        </SheetContent>
      </Sheet>

      <div className="flex-1" />
    </header>
  )
}
