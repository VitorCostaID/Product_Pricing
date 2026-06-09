import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, X, ExternalLink, TrendingUp } from 'lucide-react'
import { api } from '@/lib/api'
import { SUPPORTED_MARKETPLACES } from '@/lib/types'
import type { ProductResult, SearchResponse } from '@/lib/types'
import { clsx } from 'clsx'

const formatBRL = (v: number | null) =>
  v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function SearchPage() {
  // Removed: useAuthStore — no auth needed yet
  const [query, setQuery] = useState('')
  const [selectedMarkets, setSelectedMarkets] = useState<string[]>(['mercadolivre'])
  const [maxResults, setMaxResults] = useState(20)
  const [results, setResults] = useState<ProductResult[]>([])
  const [response, setResponse] = useState<SearchResponse | null>(null)

  const searchMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<SearchResponse>('/search/', {
        query,
        marketplaces: selectedMarkets,
        max_results: maxResults,
      })
      return data
    },
    onSuccess: (data) => {
      setResponse(data)
      setResults(data.search.results)
    },
  })

  const toggleMarket = (id: string) => {
    setSelectedMarkets((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    )
  }

  const removeResult = (id: number) => {
    setResults((prev) => prev.filter((r) => r.id !== id))
  }

  const analysis = response?.analysis

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header — simplified, no auth links */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center">
          <span className="font-bold text-brand-600 text-lg tracking-tight">Prodauto</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {/* Search card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
          {/* Search bar */}
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Ex: Samsung Galaxy A15 128GB"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchMutation.mutate()}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-brand-400 text-sm"
              />
            </div>
            <input
              type="number"
              min={1} max={100}
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-20 px-3 py-2.5 rounded-xl border border-gray-300 text-sm text-center focus:outline-none focus:ring-2 focus:ring-brand-400"
              title="Máx. resultados"
            />
            <button
              onClick={() => searchMutation.mutate()}
              disabled={!query || selectedMarkets.length === 0 || searchMutation.isPending}
              className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {searchMutation.isPending ? 'Buscando…' : 'Buscar'}
            </button>
          </div>

          {/* Marketplace pills */}
          <div className="flex flex-wrap gap-2">
            {SUPPORTED_MARKETPLACES.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => toggleMarket(id)}
                className={clsx(
                  'px-3 py-1 rounded-full text-xs font-medium border transition-all',
                  selectedMarkets.includes(id)
                    ? 'bg-brand-600 text-white border-brand-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:border-brand-400'
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {searchMutation.isError && (
            <p className="text-red-500 text-sm">Erro na busca. Verifique o servidor.</p>
          )}
        </div>

        {response && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Results list */}
            <div className="lg:col-span-2 space-y-3">
              <p className="text-sm text-gray-500">{results.length} resultado(s) — clique no ✕ para remover</p>
              {results.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-xl border border-gray-200 p-4 flex gap-4 items-start shadow-sm hover:shadow-md transition-shadow"
                >
                  {item.image_url && (
                    <img
                      src={item.image_url}
                      alt={item.title}
                      className="w-16 h-16 object-contain rounded-lg border border-gray-100 flex-shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 line-clamp-2">{item.title}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
                      <span className="text-brand-600 font-bold text-sm">
                        {item.price_brl != null ? formatBRL(item.price_brl) : item.price_raw ?? '—'}
                      </span>
                      <span className="text-xs text-gray-400">{item.marketplace}</span>
                      <span className="text-xs text-gray-400">{item.condition}</span>
                      <span className="text-xs text-gray-400">{item.shipping}</span>
                      {item.rating && <span className="text-xs text-gray-400">★ {item.rating}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <a
                      href={item.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-brand-600 transition-colors"
                    >
                      <ExternalLink size={15} />
                    </a>
                    <button
                      onClick={() => removeResult(item.id)}
                      className="text-gray-300 hover:text-red-500 transition-colors"
                    >
                      <X size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Price analysis panel */}
            {analysis && analysis.count > 0 && (
              <div className="space-y-4">
                <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-sm space-y-3">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp size={16} className="text-brand-600" />
                    <h2 className="text-sm font-semibold text-gray-800">Análise de Preços</h2>
                  </div>
                  <StatRow label="Mínimo"  value={formatBRL(analysis.min_price)} />
                  <StatRow label="Máximo"  value={formatBRL(analysis.max_price)} />
                  <StatRow label="Média"   value={formatBRL(analysis.mean_price)} />
                  <StatRow label="Mediana" value={formatBRL(analysis.median_price)} />
                  <StatRow label="Média IQR (sem outliers)" value={formatBRL(analysis.iqr_mean)} highlight />
                  <StatRow label="Piso competitivo" value={formatBRL(analysis.competitive_floor)} />
                  <hr className="border-gray-100" />
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Preço sugerido de venda</p>
                  <StatRow label="Markup 10%" value={formatBRL(analysis.suggested_price_10pct)} />
                  <StatRow label="Markup 20%" value={formatBRL(analysis.suggested_price_20pct)} />
                  <StatRow label="Markup 30%" value={formatBRL(analysis.suggested_price_30pct)} />
                  <p className="text-xs text-gray-400 mt-2">Baseado em {analysis.count} produto(s) com preço válido.</p>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function StatRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={clsx('text-sm font-semibold', highlight ? 'text-brand-600' : 'text-gray-800')}>
        {value}
      </span>
    </div>
  )
}
