import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { useTheme } from '../../context'

export default function DraggableMealCard({ meal, id }) {
  const { theme } = useTheme()
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: id || `meal-${meal.id}`,
    data: { meal, type: 'pool-meal' },
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    background: theme.colors.cream,
    borderRadius: theme.borderRadius.md,
    touchAction: 'none',
  }

  const {
    name,
    emoji,
    image,
    portions,
    defaultPortions,
    nev,
    cuisineFlag,
  } = meal

  const portionCount = portions || defaultPortions || 1

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="p-3 cursor-grab active:cursor-grabbing transition-all duration-200 hover:-translate-y-0.5"
      data-dragging={isDragging}
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
              {nev || name}
            </p>
            {cuisineFlag && (
              <span className="text-xs flex-shrink-0" style={{ color: theme.colors.textSecondary }}>{cuisineFlag}</span>
            )}
          </div>

          {portionCount > 1 && (
            <span
              className="inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium"
              style={{ background: theme.colors.secondaryLight, color: theme.colors.olive }}
            >
              🍳 {portionCount} adag
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
