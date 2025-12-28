import { colors } from '../../config/colors'
import Button from './Button'

export default function ErrorMessage({ title, message, onRetry }) {
  return (
    <div
      className="rounded-2xl p-6 text-center"
      style={{ background: colors.cream }}
    >
      <span className="text-4xl block mb-4">😕</span>
      <h3
        className="text-lg font-medium mb-2"
        style={{ color: colors.lavenderDark }}
      >
        {title || 'Something went wrong'}
      </h3>
      <p className="text-sm mb-4" style={{ color: colors.stone }}>
        {message || 'An unexpected error occurred'}
      </p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} icon="🔄">
          Try Again
        </Button>
      )}
    </div>
  )
}

// Full page error state
export function ErrorPage({ title, message, onRetry }) {
  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: colors.cream }}
    >
      <div
        className="max-w-md w-full rounded-3xl p-8 text-center"
        style={{ background: colors.warmWhite }}
      >
        <span className="text-6xl block mb-6">🍽️</span>
        <h1
          className="text-2xl font-medium mb-3"
          style={{ color: colors.lavenderDark }}
        >
          {title || 'Oops!'}
        </h1>
        <p className="mb-6" style={{ color: colors.stone }}>
          {message || 'Something went wrong while loading your meal plan.'}
        </p>
        {onRetry && (
          <Button variant="primary" onClick={onRetry} icon="🔄">
            Reload
          </Button>
        )}
      </div>
    </div>
  )
}
