/**
 * Marketplace costs store.
 * Persists to localStorage so settings survive page refresh.
 * When DB is added, this will sync to the server instead.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { MarketplaceCosts } from '@/lib/types'
import { defaultCosts } from '@/lib/types'

interface CostsState {
  configs: Record<string, MarketplaceCosts>
  getCosts: (marketplace: string) => MarketplaceCosts
  setCosts: (costs: MarketplaceCosts) => void
  resetCosts: (marketplace: string) => void
}

export const useCostsStore = create<CostsState>()(
  persist(
    (set, get) => ({
      configs: {},

      getCosts: (marketplace) =>
        get().configs[marketplace] ?? defaultCosts(marketplace),

      setCosts: (costs) =>
        set((s) => ({
          configs: { ...s.configs, [costs.marketplace]: costs },
        })),

      resetCosts: (marketplace) =>
        set((s) => {
          const next = { ...s.configs }
          delete next[marketplace]
          return { configs: next }
        }),
    }),
    { name: 'marketplace-costs' }   // localStorage key
  )
)
