import { useState } from 'react'
import { useTheme } from '../../context'

export default function PoolMealCard({
  meal,
  onDragStart,
  onDragEnd,
  onClick,
}) {
  const { theme } = useTheme()
  const [isHovered, setIsHovered] = useState(false)

  const {
    id,
    name,
    nev,
    emoji,
    image,
    portions,
    defaultPortions,
    cuisine,
    cuisineFlag,
    description,
    isSeasonal,
    mealType,
  } = meal

  const portionCount = portions || defaultPortions || 1

  return (
    <div
      className="p-3 cursor-grab transition-all duration-200"
      style={{
        background: theme.colors.cream,
        borderRadius: theme.borderRadius.md,
        boxShadow: isHovered ? theme.shadows.hover : theme.shadows.sm,
        transform: isHovered ? 'translateY(-2px)' : 'none',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onClick?.(meal)}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('meal', JSON.stringify(meal))
        onDragStart?.(meal)
      }}
      onDragEnd={() => onDragEnd?.()}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className="w-10 h-10 flex items-center justify-center text-xl flex-shrink-0"
          style={{ background: theme.colors.primaryLight, borderRadius: theme.borderRadius.md }}
        >
          {emoji || image || '🍽️'}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start gap-2">
            <p className="font-medium text-sm truncate" style={{ color: theme.colors.textPrimary }}>
              {name}
            </p>
            {(cuisine || cuisineFlag) && (
              <span className="text-xs flex-shrink-0" style={{ color: theme.colors.textSecondary }}>
                {cuisineFlag || cuisine}
              </span>
            )}
          </div>

          {/* Hungarian name / description */}
          {(nev || description) && (
            <p className="text-xs mt-0.5 truncate" style={{ color: theme.colors.textSecondary }}>
              {nev || description}
            </p>
          )}

          {/* Badges */}
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            {/* Portions badge */}
            {portionCount > 1 && (
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
                style={{ background: theme.colors.secondaryLight, color: theme.colors.olive }}
              >
                🍳 Makes {portionCount}
              </span>
            )}

            {/* Seasonal badge */}
            {isSeasonal && (
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
                style={{ background: theme.colors.wheat, color: theme.colors.terracotta }}
              >
                🌸 Seasonal
              </span>
            )}

            {/* Meal type badge */}
            {mealType && (
              <span
                className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px]"
                style={{ background: theme.colors.primaryLight, color: theme.colors.textPrimary }}
              >
                {mealType}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
