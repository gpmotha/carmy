import { colors, gradients } from '../../config/colors'

export default function LoadingSpinner({ size = 'medium', message }) {
  const sizes = {
    small: 'w-6 h-6',
    medium: 'w-10 h-10',
    large: 'w-16 h-16',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className={`${sizes[size]} rounded-full animate-spin`}
        style={{
          background: gradients.primary,
          mask: 'radial-gradient(farthest-side, transparent calc(100% - 4px), #000 0)',
          WebkitMask: 'radial-gradient(farthest-side, transparent calc(100% - 4px), #000 0)',
        }}
      />
      {message && (
        <p className="text-sm" style={{ color: colors.stone }}>
          {message}
        </p>
      )}
    </div>
  )
}

// Full page loading state
export function LoadingPage({ message = 'Loading...' }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: colors.cream }}
    >
      <div className="text-center">
        <div className="text-5xl mb-6 animate-bounce">🍳</div>
        <LoadingSpinner size="large" />
        <p className="mt-4 text-lg" style={{ color: colors.lavenderDark }}>
          {message}
        </p>
      </div>
    </div>
  )
}
