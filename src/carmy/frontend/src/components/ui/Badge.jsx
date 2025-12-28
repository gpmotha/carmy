import { useTheme } from '../../context'

export default function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
}) {
  const { theme } = useTheme()

  const baseClasses = "inline-flex items-center gap-1 font-medium rounded-full"

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-xs',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  }

  const getVariantStyles = () => {
    switch (variant) {
      case 'default':
        return { background: theme.colors.primaryLight, color: theme.colors.textPrimary }
      case 'fresh':
        return { background: theme.colors.secondaryLight, color: theme.colors.olive }
      case 'leftover':
        return { background: theme.colors.wheat, color: theme.colors.terracotta }
      case 'warning':
        return { background: `${theme.colors.terracotta}20`, color: theme.colors.terracotta }
      case 'portions':
        return { background: `${theme.colors.secondary}30`, color: theme.colors.olive }
      default:
        return {}
    }
  }

  return (
    <span
      className={`${baseClasses} ${sizeClasses[size]} ${className}`}
      style={getVariantStyles()}
    >
      {children}
    </span>
  )
}

export function PortionsBadge({ count, max }) {
  // Color based on remaining portions
  let variant = 'portions'
  if (count <= 1) variant = 'warning'
  else if (count <= 2) variant = 'leftover'

  return (
    <Badge variant={variant} size="xs">
      🍳 {count}{max && `/${max}`}
    </Badge>
  )
}
