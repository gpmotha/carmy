import { colors } from '../../config/colors'
import PoolMealCard from './PoolMealCard'

export default function SeasonalPicks({ meals = [], onMealClick }) {
  if (meals.length === 0) return null

  return (
    <div className="mb-6">
      {/* Header */}
      <div
        className="flex items-center gap-2 mb-3 pb-2 border-b"
        style={{ borderColor: colors.lavenderLight }}
      >
        <span className="text-lg">🌸</span>
        <div>
          <h4 className="text-sm font-medium" style={{ color: colors.lavenderDark }}>
            Seasonal Picks
          </h4>
          <p className="text-[10px]" style={{ color: colors.stone }}>
            Perfect for this time of year
          </p>
        </div>
      </div>

      {/* Horizontal scroll of seasonal meals */}
      <div className="flex gap-2 overflow-x-auto pb-2 -mx-2 px-2">
        {meals.map((meal) => (
          <div key={meal.id} className="flex-shrink-0 w-36">
            <SeasonalMealCard meal={meal} onClick={() => onMealClick?.(meal)} />
          </div>
        ))}
      </div>
    </div>
  )
}

function SeasonalMealCard({ meal, onClick }) {
  return (
    <div
      className="p-3 rounded-xl cursor-grab transition-all duration-200 hover:shadow-hover hover:-translate-y-0.5"
      style={{
        background: `linear-gradient(135deg, ${colors.wheat}40 0%, ${colors.sageLight}40 100%)`,
        border: `1px solid ${colors.sage}30`,
      }}
      onClick={onClick}
      draggable
    >
      <div className="text-center">
        <span className="text-2xl block mb-1">{meal.emoji || '🍽️'}</span>
        <p
          className="text-xs font-medium truncate"
          style={{ color: colors.lavenderDark }}
        >
          {meal.name}
        </p>
        {meal.portions > 1 && (
          <span
            className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px]"
            style={{ background: colors.sage + '30', color: colors.olive }}
          >
            🍳 {meal.portions}
          </span>
        )}
      </div>
    </div>
  )
}
