import { useQuery } from "@tanstack/react-query"

export interface ExchangeRates {
  /** Rates relative to USD: e.g. { BRL: 5.25, UYU: 39.5, USD: 1 } */
  rates: Record<string, number>
  date: string
}

async function fetchRates(): Promise<ExchangeRates> {
  const res = await fetch("https://open.er-api.com/v6/latest/USD")
  if (!res.ok) throw new Error(`Exchange rate fetch failed: HTTP ${res.status}`)
  const data = await res.json()
  return { rates: data.rates as Record<string, number>, date: data.time_last_update_utc as string }
}

/** Fetches USD-based exchange rates. Cached for 8 hours. */
export function useExchangeRates() {
  return useQuery<ExchangeRates>({
    queryKey: ["exchange-rates"],
    queryFn: fetchRates,
    staleTime: 8 * 60 * 60 * 1000,   // 8 hours
    gcTime: 8 * 60 * 60 * 1000,
    retry: 2,
  })
}

/**
 * Convert a minor-unit amount in any currency to USD minor units.
 * Returns null if rates are not yet loaded or currency is unknown.
 */
export function toUSDMinor(
  minor: number,
  currency: string,
  rates: Record<string, number> | undefined,
): number | null {
  if (!rates) return null
  if (currency === "USD") return minor
  const rate = rates[currency]
  if (!rate) return null
  // rate = how many currency units per 1 USD  → divide to get USD
  return Math.round(minor / rate)
}
