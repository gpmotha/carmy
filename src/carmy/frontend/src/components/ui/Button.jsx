import { useTheme } from '../../context'

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  onClick,
  disabled = false,
  className = '',
  ...props
}) {
  const { theme } = useTheme()

  const baseClasses = "inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-5 py-3 text-sm',
    lg: 'px-6 py-4 text-base',
  }

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          background: theme.gradients.primary,
          color: theme.colors.white,
          boxShadow: theme.shadows.primary,
          borderRadius: theme.borderRadius.md,
        }
      case 'secondary':
        return {
          background: theme.colors.cardBackground,
          color: theme.colors.textPrimary,
          boxShadow: theme.shadows.sm,
          borderRadius: theme.borderRadius.md,
        }
      case 'ghost':
        return {
          background: 'transparent',
          color: theme.colors.textPrimary,
          borderRadius: theme.borderRadius.md,
        }
      case 'danger':
        return {
          background: theme.colors.danger,
          color: theme.colors.white,
          boxShadow: theme.shadows.sm,
          borderRadius: theme.borderRadius.md,
        }
      default:
        return {}
    }
  }

  return (
    <button
      className={`${baseClasses} ${sizeClasses[size]} ${className}`}
      style={getVariantStyles()}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {icon && <span>{icon}</span>}
      {children}
    </button>
  )
}
