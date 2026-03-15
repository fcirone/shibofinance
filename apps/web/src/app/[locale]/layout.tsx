import type { Metadata } from "next"
import { DM_Sans, DM_Mono } from "next/font/google"
import { Suspense } from "react"
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import "../globals.css"
import { AppShell } from "@/components/shell/AppShell"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { ThemeProvider } from "@/components/providers/ThemeProvider"
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

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  if (!routing.locales.includes(locale as 'pt' | 'en' | 'es')) notFound()

  const messages = await getMessages()

  return (
    <html lang={locale} className={`${dmSans.variable} ${dmMono.variable}`} suppressHydrationWarning>
      <body className="antialiased font-sans">
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            <QueryProvider>
              <AppShell><Suspense>{children}</Suspense></AppShell>
              <Toaster richColors closeButton />
            </QueryProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
