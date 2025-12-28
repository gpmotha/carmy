import { useState } from 'react'
import { useTheme } from '../../context'

export default function Sidebar({ children, title = "Ételek", subtitle = "Húzd a napra" }) {
  const { theme } = useTheme()

  return (
    <aside
      className="h-full p-4"
      style={{ background: theme.colors.background }}
    >
      <h3
        className="text-lg font-light mb-1"
        style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif }}
      >
        {title}
      </h3>
      <p className="text-sm mb-4" style={{ color: theme.colors.textSecondary }}>{subtitle}</p>
      {children}
    </aside>
  )
}

export function SearchInput({ value, onChange, placeholder = "Ételek keresése..." }) {
  const { theme } = useTheme()

  return (
    <div className="relative mb-4">
      <span
        className="absolute left-3 top-1/2 -translate-y-1/2"
        style={{ color: theme.colors.textSecondary }}
      >
        🔍
      </span>
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-4 py-3 text-sm transition-all focus:outline-none"
        style={{
          background: theme.colors.cream,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.borderRadius.md,
          color: theme.colors.textPrimary,
        }}
      />
    </div>
  )
}

export function FilterPills({ filters, activeFilter, onFilterChange }) {
  const { theme } = useTheme()

  return (
    <div className="flex flex-wrap gap-2 mb-6">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className="px-3 py-1.5 text-xs font-medium transition-all duration-200"
          style={{
            borderRadius: theme.borderRadius.lg,
            background: activeFilter === filter.value ? theme.colors.primary : theme.colors.cream,
            color: activeFilter === filter.value ? theme.colors.white : theme.colors.textSecondary,
            boxShadow: activeFilter === filter.value ? theme.shadows.sm : 'none',
          }}
        >
          {filter.icon && <span className="mr-1">{filter.icon}</span>}
          {filter.label}
        </button>
      ))}
    </div>
  )
}

export function PoolSection({ title, count, emoji, children, defaultOpen = true }) {
  const { theme } = useTheme()
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-2 text-sm font-medium transition-colors"
        style={{ color: theme.colors.textPrimary }}
      >
        <span className="flex items-center gap-2">
          {emoji && <span>{emoji}</span>}
          {title}
        </span>
        <span className="flex items-center gap-2">
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: theme.colors.cream, color: theme.colors.textSecondary }}
          >
            {count}
          </span>
          <span className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </span>
      </button>
      {isOpen && (
        <div className="mt-2 space-y-2">
          {children}
        </div>
      )}
    </div>
  )
}
