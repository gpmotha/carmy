import { Header } from '../layout'
import { useTheme } from '../../context'

export default function BoardLayout({
  year,
  week,
  startDate,
  endDate,
  onPrev,
  onNext,
  onToday,
  sidebar,
  children,
  actions
}) {
  const { theme } = useTheme()

  return (
    <div
      className="h-screen flex flex-col overflow-hidden"
      style={{ background: theme.colors.background }}
    >
      {/* Header - compact */}
      <Header
        year={year}
        week={week}
        startDate={startDate}
        endDate={endDate}
        onPrev={onPrev}
        onNext={onNext}
        onToday={onToday}
      />

      {/* Main Content Area - fills remaining height */}
      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar (Meal Pool) - fixed width on left */}
        {sidebar && (
          <div
            className="w-80 flex-shrink-0 border-r overflow-y-auto"
            style={{ borderColor: `${theme.colors.border}30` }}
          >
            {sidebar}
          </div>
        )}

        {/* Board Grid - takes remaining width */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Week Grid - scrollable */}
          <div className="flex-1 overflow-auto p-4">
            {children}
          </div>

          {/* Action Buttons - fixed at bottom */}
          {actions && (
            <div
              className="flex-shrink-0 px-4 py-3 border-t backdrop-blur-sm"
              style={{
                borderColor: `${theme.colors.border}30`,
                background: `${theme.colors.cardBackground}80`,
              }}
            >
              <div className="flex flex-wrap gap-4 justify-between items-center">
                {actions}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
