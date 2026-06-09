// ── Auth ──────────────────────────────────────────────────────────────────

export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

// ── Search ────────────────────────────────────────────────────────────────

export const SUPPORTED_MARKETPLACES = [
  { id: 'mercadolivre', label: 'Mercado Livre' },
  { id: 'olx',         label: 'OLX' },
  { id: 'shopee',      label: 'Shopee' },
  { id: 'americanas',  label: 'Americanas' },
  { id: 'magazineluiza', label: 'Magazine Luiza' },
] as const

export type MarketplaceId = (typeof SUPPORTED_MARKETPLACES)[number]['id']

export interface SearchRequest {
  query: string
  marketplaces: MarketplaceId[]
  max_results: number
}

export interface ProductResult {
  id: number
  marketplace: string
  title: string
  link: string
  price_raw: string | null
  price_brl: number | null
  rating: string | null
  condition: string
  shipping: string
  image_url: string | null
}

export interface SearchRecord {
  id: number
  query: string
  marketplaces: string
  max_results: number
  result_count: number
  created_at: string
  results: ProductResult[]
}

export interface PriceAnalysis {
  count: number
  min_price: number | null
  max_price: number | null
  mean_price: number | null
  median_price: number | null
  iqr_mean: number | null
  competitive_floor: number | null
  suggested_price_10pct: number | null
  suggested_price_20pct: number | null
  suggested_price_30pct: number | null
  currency: string
}

export interface SearchResponse {
  search: SearchRecord
  analysis: PriceAnalysis
}
