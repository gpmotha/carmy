import { useState, useEffect, useCallback } from 'react'
import { meals } from '../api'

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

// Transform API meal to component format
function transformMeal(meal) {
  return {
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
    isVegan: meal.is_vegan,
    seasonality: meal.seasonality,
    isSeasonal: meal.seasonality && meal.seasonality !== 'year_round',
    calories: meal.calories,
    prepTime: meal.prep_time_minutes,
  }
}

// Hook for fetching all meals
export function useMeals(filters = {}) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchMeals = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await meals.getMeals(filters)
      setData(response.map(transformMeal))
    } catch (err) {
      setError(err.message || 'Failed to load meals')
      console.error('Meals fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(filters)])

  useEffect(() => {
    fetchMeals()
  }, [fetchMeals])

  return {
    meals: data,
    loading,
    error,
    refetch: fetchMeals,
  }
}

// Hook for searching meals
export function useSearchMeals() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const search = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setResults([])
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await meals.searchMeals(query)
      setResults(response.map(transformMeal))
    } catch (err) {
      setError(err.message || 'Search failed')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(() => {
    setResults([])
    setError(null)
  }, [])

  return {
    results,
    loading,
    error,
    search,
    clear,
  }
}

// Hook for meal types
export function useMealTypes() {
  const [types, setTypes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    meals
      .getMealTypes()
      .then(setTypes)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return { types, loading }
}

// Hook for cuisines
export function useCuisines() {
  const [cuisines, setCuisines] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    meals
      .getCuisines()
      .then(setCuisines)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return { cuisines, loading }
}

export default useMeals
