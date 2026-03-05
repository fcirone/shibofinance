import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AppShell } from "@/components/shell/AppShell"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "Finance OS",
  description: "Local-first personal finance dashboard",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased font-sans">
        <QueryProvider>
          <AppShell>{children}</AppShell>
          <Toaster richColors closeButton />
        </QueryProvider>
      </body>
    </html>
  )
}
