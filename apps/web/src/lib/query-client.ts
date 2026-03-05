"use client"

import { QueryClient, QueryCache } from "@tanstack/react-query"
import { toast } from "sonner"

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      const msg = error instanceof Error ? error.message : "Something went wrong"
      if (msg.includes("fetch") || msg.includes("network") || msg.includes("Failed")) {
        toast.error("Could not connect to API. Make sure the backend is running.")
      } else {
        toast.error(msg)
      }
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 0,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
