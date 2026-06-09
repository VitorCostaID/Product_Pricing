import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import type { SearchRecord } from '@/lib/types'

export default function HistoryPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['search-history'],
    queryFn: async () => {
      const { data } = await api.get<SearchRecord[]>('/search/history')
      return data
    },
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center gap-3">
          <Link to="/" className="text-gray-400 hover:text-gray-700 transition-colors">
            <ArrowLeft size={18} />
          </Link>
          <span className="font-semibold text-gray-800">Histórico de buscas</span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {isLoading && <p className="text-gray-500 text-sm">Carregando…</p>}
        {data && data.length === 0 && (
          <p className="text-gray-500 text-sm">Nenhuma busca ainda. <Link to="/" className="text-brand-600">Fazer a primeira →</Link></p>
        )}
        <div className="space-y-3">
          {data?.map((s) => (
            <Link
              key={s.id}
              to={`/?search=${s.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-gray-900 text-sm">{s.query}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {s.marketplaces.split(',').join(' · ')} · {s.result_count} resultado(s)
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Clock size={12} />
                  {new Date(s.created_at).toLocaleDateString('pt-BR')}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  )
}
