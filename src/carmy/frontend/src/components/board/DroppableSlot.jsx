import { useDroppable } from '@dnd-kit/core'
import { useTheme } from '../../context'
import MealCard from './MealCard'

export default function DroppableSlot({
  id,
  label,
  labelHu,
  meal,
  onRemove,
  onClick,
  compact = false,
}) {
  const { theme, themeName } = useTheme()
  const { isOver, setNodeRef, active } = useDroppable({
    id,
    data: { type: 'slot' },
  })

  const isDraggingMeal = active?.data?.current?.type === 'pool-meal'
  const showDropZone = isDraggingMeal && !meal

  if (compact) {
    return (
      <div ref={setNodeRef} className="relative">
        {meal ? (
          <CompactMealCard meal={meal} onRemove={onRemove} onClick={onClick} theme={theme} themeName={themeName} />
        ) : (
          <div
            className="h-10 flex items-center justify-between px-3 transition-all duration-200"
            style={{
              background: isOver
                ? `${theme.colors.primary}20`
                : showDropZone
                ? `${theme.colors.primary}10`
                : theme.colors.cream,
              border: isOver
                ? `2px dashed ${theme.colors.primary}`
                : `2px dashed ${theme.colors.primaryLight}`,
              borderRadius: theme.borderRadius.sm,
            }}
          >
            <span className="text-sm font-medium" style={{ color: theme.colors.textSecondary }}>
              {labelHu || label}
            </span>
            <span
              className={`text-sm transition-opacity ${
                isOver ? 'opacity-80' : 'opacity-30'
              }`}
              style={{ color: theme.colors.primary }}
            >
              +
            </span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div ref={setNodeRef} className="relative min-h-[70px]">
      {/* Slot Label */}
      {!meal && (
        <div className="absolute -top-1 left-2 z-10">
          <span
            className="text-xs uppercase tracking-wider px-2 py-1 font-medium"
            style={{
              background: theme.colors.primaryLight,
              color: theme.colors.textSecondary,
              borderRadius: theme.borderRadius.sm,
            }}
          >
            {labelHu || label}
          </span>
        </div>
      )}

      {/* Content */}
      {meal ? (
        <MealCard
          meal={meal}
          onRemove={onRemove}
          onClick={onClick}
        />
      ) : (
        <div
          className="h-20 flex flex-col items-center justify-center transition-all duration-200"
          style={{
            background: isOver
              ? `${theme.colors.primary}15`
              : showDropZone
              ? `${theme.colors.primary}08`
              : theme.colors.cream,
            border: isOver
              ? `2px dashed ${theme.colors.primary}`
              : showDropZone
              ? `2px dashed ${theme.colors.primary}50`
              : `2px dashed ${theme.colors.primaryLight}`,
            borderRadius: theme.borderRadius.lg,
            boxShadow: isOver ? `0 0 20px ${theme.colors.primary}30` : 'none',
          }}
        >
          <span
            className={`text-2xl transition-all duration-200 ${
              isOver ? 'scale-125 opacity-80' : showDropZone ? 'opacity-40' : 'opacity-20'
            }`}
          >
            +
          </span>
          <span
            className={`text-xs font-medium transition-opacity ${
              isOver ? 'opacity-80' : showDropZone ? 'opacity-50' : 'opacity-30'
            }`}
            style={{ color: theme.colors.textSecondary }}
          >
            {isOver ? 'Elenged!' : 'Húzd ide'}
          </span>
        </div>
      )}
    </div>
  )
}

// Compact meal card for swimlane slots
function CompactMealCard({ meal, onRemove, onClick, theme, themeName }) {
  // Use gradients for Provance theme
  const cardBackground = themeName === 'provance'
    ? (meal.isLeftover ? theme.gradients.leftover : theme.gradients.fresh)
    : (meal.isLeftover ? theme.colors.successLight : theme.colors.cardBackground)

  return (
    <div
      className="h-10 flex items-center gap-2 px-3 cursor-pointer group transition-all hover:shadow-lg"
      style={{
        background: cardBackground,
        border: meal.isLeftover ? `4px solid ${theme.colors.accentDark}` : undefined,
        borderRadius: theme.borderRadius.sm,
        boxShadow: theme.shadows.sm,
      }}
      onClick={onClick}
    >
      <span className="text-base">{meal.emoji || '🍽️'}</span>
      <span
        className="text-sm font-medium truncate flex-1"
        style={{ color: theme.colors.textPrimary }}
      >
        {meal.nev || meal.name}
      </span>
      {meal.isLeftover && (
        <span
          className="text-[9px] px-1.5 py-0.5"
          style={{
            background: theme.colors.accentDark,
            color: theme.colors.white,
            borderRadius: '4px',
          }}
        >
          M
        </span>
      )}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove?.()
        }}
        className="opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center text-xs transition-opacity"
        style={{
          background: `${theme.colors.danger}20`,
          color: theme.colors.danger,
          borderRadius: '4px',
        }}
      >
        ×
      </button>
    </div>
  )
}
