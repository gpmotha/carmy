import { useState, useEffect, useCallback } from 'react'
import { board } from '../api'

// Transform API board data to component-friendly format
function transformBoardData(data) {
  if (!data?.week?.days) return null

  const days = data.week.days.map((day, index) => {
    const slots = {}

    // Transform each slot
    Object.entries(day.slots || {}).forEach(([slotType, slotData]) => {
      if (slotData?.meal) {
        slots[slotType] = {
          planMealId: slotData.plan_meal_id,
          id: slotData.meal.id,
          name: slotData.meal.name,
          nev: slotData.meal.nev,
          emoji: getMealEmoji(slotData.meal.meal_type),
          mealType: slotData.meal.meal_type,
          portions: slotData.meal.default_portions,
          isLeftover: slotData.is_leftover,
          portionsRemaining: slotData.portions_remaining,
          chainId: slotData.chain_id,
          chainPosition: getChainPosition(slotData, day.slots, slotType),
        }
      }
    })

    return {
      date: day.date,
      dayNumber: new Date(day.date).getDate(),
      dayOfWeek: day.day_of_week,
      dayName: day.day_name,
      isToday: isToday(day.date),
      slots,
    }
  })

  return {
    year: data.week.year,
    week: data.week.week,
    startDate: data.week.start_date,
    endDate: data.week.end_date,
    planId: data.week.plan_id,
    days,
    pool: transformPool(data.pool),
    suggestions: transformMeals(data.suggestions),
    recentlyUsed: transformMeals(data.recently_used),
  }
}

// Get emoji for meal type
function getMealEmoji(mealType) {
  const emojis = {
    soup: '🍲',
    main: '🍽️',
    main_course: '🍽️',
    fozelek: '🥬',
    sweet: '🍰',
    dessert: '🍰',
    pasta: '🍝',
    salad: '🥗',
    breakfast: '🍳',
    snack: '🥪',
  }
  return emojis[mealType] || '🍽️'
}

// Determine chain position (start/middle/end)
function getChainPosition(slotData) {
  if (!slotData.chain_id) return null
  if (!slotData.is_leftover) return 'start'
  if (slotData.portions_remaining === 1) return 'end'
  return 'middle'
}

// Check if date is today
function isToday(dateStr) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const date = new Date(dateStr)
  date.setHours(0, 0, 0, 0)
  return date.getTime() === today.getTime()
}

// Transform pool data
function transformPool(pool) {
  if (!pool) return []
  return pool.map((section) => ({
    mealType: section.meal_type,
    label: section.label,
    emoji: section.emoji,
    meals: transformMeals(section.meals),
  }))
}

// Transform meals array
function transformMeals(meals) {
  if (!meals) return []
  return meals.map((meal) => ({
    id: meal.id,
    name: meal.name,
    nev: meal.nev,
    emoji: getMealEmoji(meal.meal_type),
    mealType: meal.meal_type,
    cuisine: meal.cuisine,
    cuisineFlag: getCuisineFlag(meal.cuisine),
    portions: meal.default_portions,
    keepsDays: meal.keeps_days,
    hasMeat: meal.has_meat,
    isVegetarian: meal.is_vegetarian,
    seasonality: meal.seasonality,
    isSeasonal: meal.seasonality && meal.seasonality !== 'year_round',
  }))
}

// Get flag emoji for cuisine
function getCuisineFlag(cuisine) {
  const flags = {
    hungarian: '🇭🇺',
    italian: '🇮🇹',
    french: '🇫🇷',
    german: '🇩🇪',
    spanish: '🇪🇸',
    greek: '🇬🇷',
    mexican: '🇲🇽',
    chinese: '🇨🇳',
    japanese: '🇯🇵',
    indian: '🇮🇳',
    thai: '🇹🇭',
    american: '🇺🇸',
  }
  return flags[cuisine?.toLowerCase()] || null
}

// Hook for fetching and managing board data
export function useBoard(year, week) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchBoard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await board.getWeekBoard(year, week)
      setData(transformBoardData(response))
    } catch (err) {
      setError(err.message || 'Failed to load board')
      console.error('Board fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [year, week])

  useEffect(() => {
    fetchBoard()
  }, [fetchBoard])

  // Assign meal to slot
  const assignMeal = useCallback(
    async (dayOfWeek, mealSlot, mealId, createChain = false, chainDays = 1) => {
      try {
        const result = await board.assignMealToSlot({
          year,
          week,
          day_of_week: dayOfWeek,
          meal_slot: mealSlot,
          meal_id: mealId,
          create_chain: createChain,
          chain_days: chainDays,
        })

        // Refresh board data
        await fetchBoard()
        return result
      } catch (err) {
        setError(err.message || 'Failed to assign meal')
        throw err
      }
    },
    [year, week, fetchBoard]
  )

  // Remove meal from slot
  const removeMeal = useCallback(
    async (planMealId, breakChain = false) => {
      try {
        await board.removeSlot(planMealId, breakChain)
        await fetchBoard()
      } catch (err) {
        setError(err.message || 'Failed to remove meal')
        throw err
      }
    },
    [fetchBoard]
  )

  // Update local state optimistically
  const updateDay = useCallback((dayIndex, slotType, meal) => {
    setData((prev) => {
      if (!prev) return prev
      const newDays = [...prev.days]
      const day = { ...newDays[dayIndex] }
      day.slots = {
        ...day.slots,
        [slotType]: meal,
      }
      newDays[dayIndex] = day
      return { ...prev, days: newDays }
    })
  }, [])

  return {
    data,
    loading,
    error,
    refetch: fetchBoard,
    assignMeal,
    removeMeal,
    updateDay,
  }
}

export default useBoard
