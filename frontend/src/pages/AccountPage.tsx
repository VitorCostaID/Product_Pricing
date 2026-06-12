import AppLayout from '@/components/layout/AppLayout'
import { User } from 'lucide-react'

export default function AccountPage() {
  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto px-4 py-12 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto">
          <User size={28} className="text-gray-400" />
        </div>
        <h1 className="text-xl font-bold text-gray-800">Conta</h1>
        <p className="text-sm text-gray-500">
          Login, histórico de buscas e assinatura serão adicionados em breve.
        </p>
      </div>
    </AppLayout>
  )
}
