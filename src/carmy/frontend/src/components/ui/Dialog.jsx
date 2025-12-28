import { useEffect, useRef } from 'react'
import { useTheme } from '../../context'

export default function Dialog({
  isOpen,
  onClose,
  title,
  children,
}) {
  const { theme } = useTheme()
  const dialogRef = useRef(null)

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose?.()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose?.()
      }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        style={{ animation: 'fadeIn 0.2s ease-out' }}
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-md p-6 shadow-2xl"
        style={{
          background: theme.colors.cardBackground,
          borderRadius: theme.borderRadius.lg,
          animation: 'slideUp 0.3s ease-out',
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center text-lg transition-colors"
          style={{ color: theme.colors.textSecondary }}
        >
          ×
        </button>

        {/* Title */}
        {title && (
          <h2
            className="text-xl font-light mb-4 pr-8"
            style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif }}
          >
            {title}
          </h2>
        )}

        {/* Content */}
        {children}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  )
}
