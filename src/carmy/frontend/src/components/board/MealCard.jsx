import { useState } from 'react'
import { useTheme } from '../../context'

export default function MealCard({
  meal,
  onRemove,
  onClick,
  isDragging = false,
}) {
  const { theme, themeName } = useTheme()
  const [isHovered, setIsHovered] = useState(false)

  const {
    name,
    nev,
    image,
    emoji,
    portions,
    portionsRemaining,
    isLeftover = false,
    chainPosition, // 'start' | 'middle' | 'end' | null
  } = meal

  // Determine card style based on leftover status and theme
  const cardBackground = themeName === 'provance'
    ? (isLeftover ? theme.gradients.leftover : theme.gradients.fresh)
    : (isLeftover ? theme.colors.successLight : theme.colors.cardBackground)

  // Chain indicator colors
  const chainColors = {
    start: theme.colors.secondary, // Green - fresh cook
    middle: theme.colors.wheat, // Yellow - middle of chain
    end: theme.colors.terracotta, // Orange/red - last portion
  }

  const chainBorderColor = chainPosition ? chainColors[chainPosition] : 'transparent'

  // Portions badge color
  const getPortionsBadgeStyle = () => {
    if (!portionsRemaining) return {}
    if (portionsRemaining <= 1) {
      return { background: `${theme.colors.terracotta}30`, color: theme.colors.terracotta }
    }
    if (portionsRemaining <= 2) {
      return { background: theme.colors.wheat, color: theme.colors.terracotta }
    }
    return { background: `${theme.colors.secondary}30`, color: theme.colors.olive }
  }

  return (
    <div
      className={`p-3 cursor-grab relative group transition-all duration-200
        ${isDragging ? 'opacity-50 scale-95' : ''}`}
      style={{
        background: cardBackground,
        borderRadius: theme.borderRadius.md,
        borderLeft: chainPosition ? `4px solid ${chainBorderColor}` : undefined,
        boxShadow: isHovered ? theme.shadows.hover : theme.shadows.sm,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      draggable
    >
      {/* Remove Button */}
      <button
        className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full shadow-md
                   flex items-center justify-center text-xs
                   opacity-0 group-hover:opacity-100 transition-opacity"
        style={{
          background: theme.colors.white,
          color: theme.colors.textSecondary,
        }}
        onClick={(e) => {
          e.stopPropagation()
          onRemove?.()
        }}
      >
        ×
      </button>

      {/* Meal Content */}
      <div className="flex items-center gap-2">
        <span className="text-xl flex-shrink-0">{emoji || image || '🍽️'}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: theme.colors.textPrimary }}>
            {nev || name}
          </p>

          {/* Badges */}
          <div className="flex items-center gap-1.5 mt-1">
            {/* Leftover badge */}
            {isLeftover && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded-full"
                style={{ background: `${theme.colors.terracotta}30`, color: theme.colors.terracotta }}
              >
                ♻️ Maradék
              </span>
            )}

            {/* Fresh cook badge */}
            {!isLeftover && chainPosition === 'start' && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded-full"
                style={{ background: `${theme.colors.secondary}30`, color: theme.colors.olive }}
              >
                🍳 Friss
              </span>
            )}

            {/* Portions badge */}
            {portionsRemaining && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                style={getPortionsBadgeStyle()}
              >
                {portionsRemaining} maradt
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Chain Indicator Line */}
      {chainPosition && chainPosition !== 'end' && (
        <div
          className="absolute right-0 top-1/2 w-4 h-0.5"
          style={{ background: chainBorderColor }}
        />
      )}
    </div>
  )
}
