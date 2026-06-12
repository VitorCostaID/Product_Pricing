/**
 * MarketplaceBadge — shows marketplace logo with fallback text badge.
 * Logo images are loaded from external URLs with an object-contain fit.
 */
import { getMarketplace } from '@/lib/types'

interface Props {
  marketplace: string
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: { img: 'h-5 w-14', text: 'text-xs px-2 py-0.5' },
  md: { img: 'h-7 w-20', text: 'text-sm px-3 py-1'   },
  lg: { img: 'h-10 w-28', text: 'text-base px-4 py-1.5' },
}

export default function MarketplaceBadge({ marketplace, size = 'md' }: Props) {
  const mp = getMarketplace(marketplace)
  const s = sizes[size]

  if (!mp) {
    return (
      <span className={`inline-block rounded-full bg-gray-200 text-gray-600 font-medium ${s.text}`}>
        {marketplace}
      </span>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <img
        src={mp.logo}
        alt={mp.label}
        className={`${s.img} object-contain rounded`}
        onError={(e) => {
          // If logo fails to load, hide image and show text fallback
          const el = e.currentTarget
          el.style.display = 'none'
          el.nextElementSibling?.removeAttribute('hidden')
        }}
      />
      <span
        hidden
        className={`inline-block rounded-full font-medium ${s.text}`}
        style={{ background: mp.color, color: mp.textColor }}
      >
        {mp.label}
      </span>
    </div>
  )
}
