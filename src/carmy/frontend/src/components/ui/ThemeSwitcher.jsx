import { useTheme } from '../../context'

export default function ThemeSwitcher() {
  const { themeName, setTheme, theme } = useTheme()

  return (
    <div
      className="fixed bottom-4 left-4 flex gap-2 p-1 z-50"
      style={{
        background: theme.colors.cardBackground,
        borderRadius: theme.borderRadius.sm,
        boxShadow: theme.shadows.card,
        border: `1px solid ${theme.colors.border}`,
      }}
    >
      <ThemeButton
        name="Provance"
        isActive={themeName === 'provance'}
        onClick={() => setTheme('provance')}
        theme={theme}
        color="#9B7BB8"
      />
      <ThemeButton
        name="Bear"
        isActive={themeName === 'bear'}
        onClick={() => setTheme('bear')}
        theme={theme}
        color="#1C2A39"
      />
    </div>
  )
}

function ThemeButton({ name, isActive, onClick, theme, color }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-3 py-2 text-sm font-medium transition-all"
      style={{
        background: isActive ? theme.colors.primary : 'transparent',
        color: isActive ? theme.colors.white : theme.colors.textSecondary,
        borderRadius: theme.borderRadius.sm,
        border: 'none',
        cursor: 'pointer',
      }}
    >
      <span
        className="w-3 h-3 rounded-full"
        style={{
          background: color,
          border: isActive ? '2px solid white' : `1px solid ${theme.colors.border}`,
        }}
      />
      {name}
    </button>
  )
}
