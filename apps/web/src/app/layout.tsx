import type { Metadata } from "next"
import { DM_Sans, DM_Mono } from "next/font/google"
import { Suspense } from "react"
import "./globals.css"
import { AppShell } from "@/components/shell/AppShell"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { Toaster } from "@/components/ui/sonner"

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
})

const dmMono = DM_Mono({
  subsets: ["latin"],
  variable: "--font-dm-mono",
  weight: ["400", "500"],
  display: "swap",
})

export const metadata: Metadata = {
  title: "Shibo Finance",
  description: "Local-first personal finance dashboard",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`dark ${dmSans.variable} ${dmMono.variable}`}>
      <body className="antialiased font-sans">
        <QueryProvider>
          <AppShell><Suspense>{children}</Suspense></AppShell>
          <Toaster richColors closeButton />
        </QueryProvider>
      </body>
    </html>
  )
}
