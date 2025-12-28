import { colors, gradients } from '../../config/colors'

export default function DragOverlayContent({ meal }) {
  if (!meal) return null

  const { name, nev, emoji, image, portions, defaultPortions } = meal
  const portionCount = portions || defaultPortions || 1

  return (
    <div
      className="p-3 rounded-xl shadow-2xl cursor-grabbing"
      style={{
        background: gradients.primary,
        color: 'white',
        transform: 'rotate(3deg) scale(1.05)',
        width: '200px',
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
          style={{ background: 'rgba(255,255,255,0.2)' }}
        >
          {emoji || image || '🍽️'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{nev || name}</p>
          {portionCount > 1 && (
            <span className="text-[10px] opacity-80">
              🍳 {portionCount} adag
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
