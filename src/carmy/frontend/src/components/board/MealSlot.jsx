import { colors } from '../../config/colors'
import MealCard from './MealCard'
import EmptySlot from './EmptySlot'

export default function MealSlot({
  label,
  labelHu,
  slot,
  meal,
  onDrop,
  onRemove,
  onClick,
  isDragOver = false,
}) {
  return (
    <div className="relative">
      {/* Slot Label (shown only when empty) */}
      {!meal && (
        <div className="absolute -top-1 left-2 z-10">
          <span
            className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded"
            style={{
              background: colors.lavenderLight,
              color: colors.stone,
            }}
          >
            {labelHu || label}
          </span>
        </div>
      )}

      {/* Slot Content */}
      {meal ? (
        <MealCard
          meal={meal}
          onRemove={onRemove}
          onClick={onClick}
        />
      ) : (
        <EmptySlot
          isDragOver={isDragOver}
          onDrop={onDrop}
        />
      )}
    </div>
  )
}
