import { useTheme } from '../../context'

export default function Header({ year, week, startDate, endDate, onPrev, onNext, onToday }) {
  const { theme, themeName } = useTheme()

  return (
    <header
      className="relative overflow-hidden flex-shrink-0 border-b"
      style={{
        background: theme.colors.cardBackground,
        borderColor: `${theme.colors.border}50`,
      }}
    >
      {/* Gradient overlay for Provance */}
      {themeName === 'provance' && (
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{ background: theme.gradients.header }}
        />
      )}

      <div className="px-6 py-4 relative flex justify-between items-center">
        {/* Logo and Nav */}
        <div className="flex items-center gap-6 flex-1">
          <a
            href="/"
            className="text-3xl font-medium tracking-wide"
            style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif, textDecoration: 'none' }}
          >
            Carmy
          </a>
          <nav className="flex items-center gap-1">
            <NavLink href="/" theme={theme} themeName={themeName}>
              Étlap
            </NavLink>
            <NavLink href="/meals" theme={theme} themeName={themeName}>
              Ételek
            </NavLink>
          </nav>
        </div>

        {/* EVERY SECOND COUNTS - Center */}
        <div className="flex-1 flex justify-center">
          <div
            className="px-4 py-2"
            style={{
              background: themeName === 'provance' ? 'rgba(51, 65, 85, 0.9)' : theme.colors.primary,
              borderRadius: theme.borderRadius.sm,
            }}
          >
            <span
              className="text-sm font-medium tracking-widest uppercase"
              style={{
                color: '#22d3ee',
                textShadow: '0 0 8px rgba(34, 211, 238, 0.6)',
              }}
            >
              EVERY SECOND COUNTS
            </span>
          </div>
        </div>

        {/* Week Info + Navigation */}
        <div className="flex items-center gap-6 flex-1 justify-end">
          {/* Week Display */}
          <div className="text-right">
            <p
              className="text-xl font-medium"
              style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif }}
            >
              {week}. hét
            </p>
            <p className="text-sm" style={{ color: theme.colors.textSecondary }}>
              {startDate} – {endDate}
            </p>
          </div>

          {/* Navigation Buttons */}
          <div className="flex gap-2">
            <NavButton onClick={onPrev} aria-label="Előző hét" theme={theme} themeName={themeName}>
              ←
            </NavButton>
            <NavButton onClick={onToday} primary theme={theme} themeName={themeName}>
              Ma
            </NavButton>
            <NavButton onClick={onNext} aria-label="Következő hét" theme={theme} themeName={themeName}>
              →
            </NavButton>
          </div>
        </div>
      </div>
    </header>
  )
}

function NavButton({ children, onClick, primary = false, theme, themeName, ...props }) {
  const baseStyle = {
    padding: '8px 16px',
    borderRadius: theme.borderRadius.sm,
    fontWeight: '500',
    fontSize: '14px',
    transition: 'all 0.2s ease',
    cursor: 'pointer',
    border: 'none',
  }

  const style = primary
    ? {
        ...baseStyle,
        background: themeName === 'provance' ? theme.gradients.primary : theme.colors.primary,
        color: theme.colors.white,
        boxShadow: theme.shadows.primary,
      }
    : {
        ...baseStyle,
        background: theme.colors.cardBackground,
        color: theme.colors.textPrimary,
        border: `1px solid ${theme.colors.border}`,
        boxShadow: theme.shadows.sm,
      }

  return (
    <button style={style} onClick={onClick} {...props}>
      {children}
    </button>
  )
}

function NavLink({ children, href, theme, themeName }) {
  const isActive = typeof window !== 'undefined' && window.location.pathname === href

  return (
    <a
      href={href}
      className="px-3 py-2 text-sm font-medium transition-colors"
      style={{
        color: isActive ? theme.colors.primary : theme.colors.textSecondary,
        textDecoration: 'none',
        borderRadius: theme.borderRadius.sm,
        background: isActive ? `${theme.colors.primary}10` : 'transparent',
      }}
    >
      {children}
    </a>
  )
}
