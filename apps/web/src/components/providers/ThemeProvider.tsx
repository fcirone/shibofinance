"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="data-theme"
      defaultTheme="dark"
      themes={["light", "dark", "nord", "rose"]}
      enableSystem={false}
    >
      {children}
    </NextThemesProvider>
  )
}
