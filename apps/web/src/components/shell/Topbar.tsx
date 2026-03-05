"use client"

import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Sidebar } from "./Sidebar"

interface TopbarProps {
  onToggleCollapse?: () => void
}

export function Topbar({ onToggleCollapse }: TopbarProps) {
  return (
    <header className="flex items-center h-14 border-b border-border bg-background px-4 gap-3 shrink-0">
      {/* Desktop collapse toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="hidden lg:flex"
        onClick={onToggleCollapse}
        aria-label="Toggle sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile hamburger — opens sheet */}
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-56">
          <Sidebar />
        </SheetContent>
      </Sheet>

      {/* Spacer */}
      <div className="flex-1" />
    </header>
  )
}
