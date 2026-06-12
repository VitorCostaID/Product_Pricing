/**
 * CostsPanel — collapsible cost configuration for one marketplace.
 * Saves to localStorage via costsStore.
 */
import { useState } from 'react'
import { ChevronDown, ChevronUp, RotateCcw } from 'lucide-react'
import { useCostsStore } from '@/store/costsStore'
import MarketplaceBadge from './MarketplaceBadge'
import type { MarketplaceCosts } from '@/lib/types'

interface Props {
  marketplace: string
}

function Field({
  label, value, onChange, suffix,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  suffix: string
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <label className="text-xs text-gray-600 flex-1">{label}</label>
      <div className="flex items-center gap-1">
        <input
          type="number"
          min={0}
          step={0.01}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          className="w-24 px-2 py-1 text-sm border border-gray-300 rounded-lg
                     focus:outline-none focus:ring-2 focus:ring-brand-400 text-right"
        />
        <span className="text-xs text-gray-400 w-6">{suffix}</span>
      </div>
    </div>
  )
}

export default function CostsPanel({ marketplace }: Props) {
  const [open, setOpen] = useState(false)
  const { getCosts, setCosts, resetCosts } = useCostsStore()
  const costs = getCosts(marketplace)

  const update = (field: keyof MarketplaceCosts, value: number | string) => {
    setCosts({ ...costs, [field]: value })
  }

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3
                   bg-white hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <MarketplaceBadge marketplace={marketplace} size="sm" />
          <span className="text-sm font-medium text-gray-700">
            Custos — {costs.config_name}
          </span>
        </div>
        {open ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
      </button>

      {/* Body */}
      {open && (
        <div className="bg-gray-50 px-4 py-4 space-y-3 border-t border-gray-200">
          <div className="flex items-center justify-between mb-1">
            <input
              type="text"
              value={costs.config_name}
              onChange={(e) => update('config_name', e.target.value)}
              className="text-xs font-medium border border-gray-200 rounded px-2 py-1
                         bg-white focus:outline-none focus:ring-1 focus:ring-brand-400"
              placeholder="Nome da configuração"
            />
            <button
              onClick={() => resetCosts(marketplace)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition-colors"
            >
              <RotateCcw size={12} /> Resetar
            </button>
          </div>

          <Field
            label="Comissão da plataforma"
            value={costs.commission_pct}
            onChange={(v) => update('commission_pct', v)}
            suffix="%"
          />
          <Field
            label="Impostos"
            value={costs.tax_pct}
            onChange={(v) => update('tax_pct', v)}
            suffix="%"
          />
          <Field
            label="Taxa fixa por venda"
            value={costs.fixed_fee}
            onChange={(v) => update('fixed_fee', v)}
            suffix="R$"
          />
          <Field
            label="Custo de envio médio"
            value={costs.shipping_cost}
            onChange={(v) => update('shipping_cost', v)}
            suffix="R$"
          />
          <Field
            label="Outros custos"
            value={costs.extra_costs}
            onChange={(v) => update('extra_costs', v)}
            suffix="R$"
          />

          <p className="text-xs text-gray-400 pt-1">
            Configurações salvas automaticamente no navegador.
          </p>
        </div>
      )}
    </div>
  )
}
