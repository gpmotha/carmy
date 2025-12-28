import { useState } from 'react'
import { useTheme } from '../../context'
import DroppableSlot from './DroppableSlot'

export default function DayCard({
  dayIndex,
  date,
  dayName,
  dayNumber,
  isToday = false,
  hint,
  slots = {},
  onMealRemove,
  onMealClick,
}) {
  const { theme, themeName } = useTheme()
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className="overflow-hidden transition-all duration-300 flex flex-col h-full"
      style={{
        background: theme.colors.cardBackground,
        borderRadius: theme.borderRadius.md,
        boxShadow: isHovered ? theme.shadows.hover : theme.shadows.card,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Day Header */}
      <div
        className="p-2 text-center"
        style={{
          background: isToday
            ? (themeName === 'provance' ? theme.gradients.primary : theme.colors.primary)
            : theme.colors.primaryLight,
          color: isToday ? theme.colors.white : theme.colors.textPrimary,
          borderBottom: `1px solid ${theme.colors.border}`,
        }}
      >
        <p
          className="text-2xl font-medium"
          style={{ fontFamily: theme.fontSerif }}
        >
          {dayNumber}
        </p>
        <p className="text-xs uppercase tracking-wider opacity-80 font-medium">
          {dayName}
        </p>
      </div>

      {/* Day Hint - always show placeholder for consistent height */}
      <div
        className="px-2 py-2 text-center"
        style={{
          borderBottom: `1px solid ${theme.colors.border}`,
          background: hint ? `${theme.colors.success}15` : 'transparent',
          minHeight: '32px',
        }}
      >
        {hint ? (
          <p
            className="text-sm font-medium"
            style={{ color: theme.colors.olive, fontFamily: theme.fontSerif }}
          >
            {hint}
          </p>
        ) : (
          <p className="text-sm" style={{ color: 'transparent' }}>
            &nbsp;
          </p>
        )}
      </div>

      {/* Meal Swimlanes */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Reggeli (Breakfast) */}
        <MealSwimlane
          title="Reggeli"
          dayIndex={dayIndex}
          slots={[
            { id: 'breakfast', label: 'Reggeli', meal: slots.breakfast },
          ]}
          onMealRemove={onMealRemove}
          onMealClick={onMealClick}
          theme={theme}
          color={theme.colors.breakfast}
        />

        {/* Ebéd (Lunch) - with sub-slots */}
        <MealSwimlane
          title="Ebéd"
          dayIndex={dayIndex}
          slots={[
            { id: 'lunch_appetizer', label: 'Előétel', meal: slots.lunch_appetizer },
            { id: 'lunch_soup', label: 'Leves', meal: slots.lunch_soup },
            { id: 'lunch_main', label: 'Főétel', meal: slots.lunch_main },
            { id: 'lunch_dessert', label: 'Desszert', meal: slots.lunch_dessert },
          ]}
          onMealRemove={onMealRemove}
          onMealClick={onMealClick}
          theme={theme}
          color={theme.colors.lunch}
        />

        {/* Vacsora (Dinner) - with sub-slots */}
        <MealSwimlane
          title="Vacsora"
          dayIndex={dayIndex}
          slots={[
            { id: 'dinner_appetizer', label: 'Előétel', meal: slots.dinner_appetizer },
            { id: 'dinner_soup', label: 'Leves', meal: slots.dinner_soup },
            { id: 'dinner_main', label: 'Főétel', meal: slots.dinner_main },
            { id: 'dinner_dessert', label: 'Desszert', meal: slots.dinner_dessert },
          ]}
          onMealRemove={onMealRemove}
          onMealClick={onMealClick}
          theme={theme}
          color={theme.colors.dinner}
        />
      </div>
    </div>
  )
}

// Swimlane component for meal sections
function MealSwimlane({ title, dayIndex, slots, onMealRemove, onMealClick, theme, color }) {
  return (
    <div
      className="flex-1 flex flex-col"
      style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}
    >
      {/* Swimlane Header */}
      <div
        className="px-2 py-2 text-center"
        style={{ background: `${color}20` }}
      >
        <p
          className="text-sm font-semibold"
          style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif }}
        >
          {title}
        </p>
      </div>

      {/* Slots */}
      <div className="flex-1 p-1 space-y-1 overflow-y-auto">
        {slots.map(({ id, label, meal }) => (
          <DroppableSlot
            key={id}
            id={`${dayIndex}-${id}`}
            label={label}
            labelHu={label}
            meal={meal}
            onRemove={() => onMealRemove?.(id)}
            onClick={() => onMealClick?.(id, meal)}
            compact
          />
        ))}
      </div>
    </div>
  )
}
