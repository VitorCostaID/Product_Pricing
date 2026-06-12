/**
 * Global search store — keeps last search results in memory
 * so the Perfect Product page can access them without re-fetching.
 */
import { create } from 'zustand'
import type { ProductResult, SearchResponse } from '@/lib/types'

interface SearchState {
  lastResponse: SearchResponse | null
  visibleResults: ProductResult[]
  purchasePrice: number | null
  setResponse: (r: SearchResponse) => void
  removeResult: (id: number) => void
  setPurchasePrice: (p: number | null) => void
  clear: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  lastResponse: null,
  visibleResults: [],
  purchasePrice: null,

  setResponse: (r) =>
    set({ lastResponse: r, visibleResults: r.search.results }),

  removeResult: (id) =>
    set((s) => ({ visibleResults: s.visibleResults.filter((r) => r.id !== id) })),

  setPurchasePrice: (p) => set({ purchasePrice: p }),

  clear: () => set({ lastResponse: null, visibleResults: [], purchasePrice: null }),
}))
