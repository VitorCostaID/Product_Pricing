import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export default function RegisterPage() {
  const { register, isLoading } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await register(email, password, fullName || undefined)
      navigate('/')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Erro ao criar conta.')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white w-full max-w-sm rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-brand-600">Criar conta</h1>
          <p className="text-sm text-gray-500 mt-1">Grátis, sem cartão de crédito.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Nome (opcional)</label>
            <input
              type="text"
              value={fullName} onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Email</label>
            <input
              type="email" required autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Senha (mín. 8 caracteres)</label>
            <input
              type="password" required minLength={8} autoComplete="new-password"
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
          </div>
          {error && <p className="text-red-500 text-xs">{error}</p>}
          <button
            type="submit" disabled={isLoading}
            className="w-full py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Criando…' : 'Criar conta'}
          </button>
        </form>
        <p className="text-center text-xs text-gray-500">
          Já tem conta?{' '}
          <Link to="/login" className="text-brand-600 font-medium hover:underline">Entrar</Link>
        </p>
      </div>
    </div>
  )
}
