import { useState } from 'react'
import { useTheme } from '../../context'
import Dialog from './Dialog'
import Button from './Button'

export default function PortionDialog({
  isOpen,
  onClose,
  meal,
  dayIndex,
  slotType,
  maxDays = 7,
  onConfirm,
}) {
  const { theme, themeName } = useTheme()
  const [selectedDays, setSelectedDays] = useState(meal?.portions || meal?.defaultPortions || 1)

  if (!meal) return null

  const portions = meal.portions || meal.defaultPortions || 1
  const remainingDays = maxDays - dayIndex
  const maxChainDays = Math.min(portions, remainingDays)

  const handleConfirm = (createChain) => {
    onConfirm?.({
      meal,
      dayIndex,
      slotType,
      createChain,
      chainDays: createChain ? selectedDays : 1,
    })
    onClose?.()
  }

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="Étel hozzáadása">
      {/* Meal Preview */}
      <div
        className="p-4 mb-6 flex items-center gap-4"
        style={{ background: theme.colors.cream, borderRadius: theme.borderRadius.md }}
      >
        <span className="text-4xl">{meal.emoji || '🍽️'}</span>
        <div>
          <p className="font-medium" style={{ color: theme.colors.textPrimary }}>
            {meal.nev || meal.name}
          </p>
          <div
            className="inline-flex items-center gap-1 mt-2 px-2 py-1 rounded-full text-xs"
            style={{ background: theme.colors.secondaryLight, color: theme.colors.olive }}
          >
            🍳 {portions} adag
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {/* Single day option */}
        <button
          onClick={() => handleConfirm(false)}
          className="w-full p-4 text-left transition-all hover:shadow-md"
          style={{
            background: theme.colors.primaryLight,
            border: `2px solid transparent`,
            borderRadius: theme.borderRadius.md,
          }}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">📍</span>
            <div>
              <p className="font-medium" style={{ color: theme.colors.textPrimary }}>
                Csak erre a napra
              </p>
              <p className="text-sm" style={{ color: theme.colors.textSecondary }}>
                Hozzáadás csak a kiválasztott helyre
              </p>
            </div>
          </div>
        </button>

        {/* Chain option (only for multi-portion meals) */}
        {portions > 1 && maxChainDays > 1 && (
          <div
            className="p-4"
            style={{
              background: themeName === 'provance' ? theme.gradients.fresh : theme.colors.secondaryLight,
              border: `2px solid ${theme.colors.secondary}40`,
              borderRadius: theme.borderRadius.md,
            }}
          >
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">📅</span>
              <div>
                <p className="font-medium" style={{ color: theme.colors.textPrimary }}>
                  Több napra kitöltés
                </p>
                <p className="text-sm" style={{ color: theme.colors.textSecondary }}>
                  Maradék lánc létrehozása
                </p>
              </div>
            </div>

            {/* Days slider */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span style={{ color: theme.colors.textSecondary }}>Napok:</span>
                <span className="font-medium" style={{ color: theme.colors.textPrimary }}>
                  {selectedDays} nap
                </span>
              </div>
              <input
                type="range"
                min={2}
                max={maxChainDays}
                value={selectedDays}
                onChange={(e) => setSelectedDays(parseInt(e.target.value))}
                className="w-full"
                style={{ accentColor: theme.colors.primary }}
              />
              <div className="flex justify-between text-xs mt-1" style={{ color: theme.colors.textSecondary }}>
                <span>2</span>
                <span>{maxChainDays}</span>
              </div>
            </div>

            {/* Chain preview */}
            <div className="flex gap-1 mb-4 overflow-x-auto pb-2">
              {Array.from({ length: selectedDays }).map((_, i) => (
                <div
                  key={i}
                  className="flex-shrink-0 w-12 h-12 flex flex-col items-center justify-center text-xs"
                  style={{
                    background: i === 0 ? theme.colors.secondary : theme.colors.wheat,
                    color: i === 0 ? theme.colors.white : theme.colors.terracotta,
                    borderLeft: i > 0 ? `3px solid ${theme.colors.terracotta}` : undefined,
                    borderRadius: theme.borderRadius.sm,
                  }}
                >
                  <span className="text-sm">{i === 0 ? '🍳' : '♻️'}</span>
                  <span className="font-medium">{portions - i}</span>
                </div>
              ))}
            </div>

            <Button
              variant="primary"
              onClick={() => handleConfirm(true)}
              className="w-full"
              icon="✨"
            >
              {selectedDays} nap kitöltése
            </Button>
          </div>
        )}
      </div>

      {/* Cancel */}
      <button
        onClick={onClose}
        className="w-full mt-4 py-3 text-sm transition-colors"
        style={{ color: theme.colors.textSecondary, borderRadius: theme.borderRadius.md }}
      >
        Mégse
      </button>
    </Dialog>
  )
}
