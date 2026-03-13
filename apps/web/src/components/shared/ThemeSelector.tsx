"use client"

import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { Palette } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

const THEMES = [
  {
    id: "dark",
    label: "Obsidian",
    description: "Deep navy · Amber gold",
    swatches: ["#0e1220", "#1e2435", "#c8a84b"],
  },
  {
    id: "light",
    label: "Ivory",
    description: "Warm white · Amber",
    swatches: ["#f8f4f0", "#ffffff", "#8a5e28"],
  },
  {
    id: "nord",
    label: "Nord",
    description: "Arctic dark · Frost blue",
    swatches: ["#2e3440", "#3b4252", "#81a1c1"],
  },
  {
    id: "rose",
    label: "Rosé Pine",
    description: "Purple dark · Love rose",
    swatches: ["#191724", "#1f1d2e", "#eb6f92"],
  },
] as const

interface ThemeSelectorProps {
  collapsed?: boolean
}

export function ThemeSelector({ collapsed = false }: ThemeSelectorProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  const current = THEMES.find((t) => t.id === theme) ?? THEMES[0]

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size={collapsed ? "icon" : "sm"}
          className={cn(
            "text-sidebar-foreground/60 hover:text-sidebar-foreground/90 hover:bg-sidebar-accent",
            collapsed ? "h-9 w-9" : "h-8 w-full justify-start gap-2 px-2.5",
          )}
          title="Change theme"
          aria-label="Change theme"
        >
          {/* Live swatch preview */}
          {mounted ? (
            <span className="flex items-center gap-0.5 shrink-0">
              {current.swatches.map((color, i) => (
                <span
                  key={i}
                  className="h-3 w-3 rounded-full ring-1 ring-black/10"
                  style={{ backgroundColor: color }}
                />
              ))}
            </span>
          ) : (
            <Palette className="h-[15px] w-[15px] shrink-0" />
          )}
          {!collapsed && (
            <span className="text-[12px] font-medium truncate">
              {mounted ? current.label : "Theme"}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent
        side="top"
        align="start"
        sideOffset={8}
        className="w-52 p-1.5"
      >
        <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Theme
        </p>
        <div className="space-y-px mt-1">
          {THEMES.map((t) => {
            const active = mounted && theme === t.id
            return (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={cn(
                  "w-full flex items-center gap-2.5 rounded-md px-2 py-1.5 text-left transition-colors",
                  active
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-accent/60 hover:text-accent-foreground",
                )}
              >
                {/* Color swatches */}
                <span className="flex items-center gap-0.5 shrink-0">
                  {t.swatches.map((color, i) => (
                    <span
                      key={i}
                      className="h-4 w-4 rounded-full ring-1 ring-black/10"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </span>
                <span className="min-w-0">
                  <span className="block text-[13px] font-medium leading-none">
                    {t.label}
                  </span>
                  <span className="block text-[10px] text-muted-foreground mt-0.5 leading-none">
                    {t.description}
                  </span>
                </span>
                {active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                )}
              </button>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
