"use client"

import { useState } from "react"
import { useTranslations } from 'next-intl'
import { Sidebar } from "./Sidebar"
import { Topbar } from "./Topbar"

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const tc = useTranslations('common')

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Skip-to-content for a11y */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-2 focus:bg-background focus:text-foreground"
      >
        {tc('skipToContent')}
      </a>

      {/* Sidebar — hidden on mobile, visible lg+ */}
      <div className="hidden lg:flex flex-col h-full shrink-0">
        <Sidebar collapsed={collapsed} />
      </div>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Topbar
          onToggleCollapse={() => setCollapsed((c) => !c)}
          collapsed={collapsed}
        />
        <main
          id="main-content"
          className="flex-1 overflow-y-auto p-5 md:p-7"
        >
          {children}
        </main>
      </div>
    </div>
  )
}
