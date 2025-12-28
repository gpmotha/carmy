import DayCard from './DayCard'

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_NAMES_HU = ['Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat', 'Vasárnap']

// Day hints based on Hungarian meal planning traditions
const DEFAULT_HINTS = {
  0: 'Maradék', // Monday - leftovers
  1: 'Főzelék nap', // Tuesday - vegetable stew
  2: null,
  3: null,
  4: null,
  5: 'Hal nap', // Saturday - fish
  6: 'Hús + saláta', // Sunday - meat + salad
}

export default function WeekGrid({
  days = [],
  year,
  week,
  onSlotDrop,
  onMealRemove,
  onMealClick,
}) {
  // Generate days if not provided
  const weekDays = days.length > 0 ? days : generateWeekDays(year, week)

  return (
    <div className="h-full grid grid-cols-7 gap-2">
      {weekDays.map((day, index) => (
        <DayCard
          key={day.date || index}
          dayIndex={index}
          date={day.date}
          dayName={DAY_NAMES_HU[index]}
          dayNumber={day.dayNumber}
          isToday={day.isToday}
          hint={day.hint || DEFAULT_HINTS[index]}
          slots={day.slots || {}}
          onMealRemove={(slot) => onMealRemove?.(index, slot)}
          onMealClick={(slot, meal) => onMealClick?.(index, slot, meal)}
        />
      ))}
    </div>
  )
}

// Helper to generate week days for display
function generateWeekDays(year, week) {
  const jan1 = new Date(year, 0, 1)
  const daysOffset = (jan1.getDay() || 7) - 1
  const firstMonday = new Date(year, 0, 1 + (7 - daysOffset))
  const startDate = new Date(firstMonday)
  startDate.setDate(firstMonday.getDate() + (week - 1) * 7)

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const days = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)

    days.push({
      date: date.toISOString().split('T')[0],
      dayNumber: date.getDate(),
      isToday: date.getTime() === today.getTime(),
      slots: {},
    })
  }

  return days
}
