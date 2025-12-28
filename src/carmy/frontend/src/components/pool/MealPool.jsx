import { useState, useMemo } from 'react'
import { useTheme } from '../../context'
import { SearchInput } from '../layout'
import { DraggableMealCard } from '../board'

// Meal type configurations with order - Hungarian UI
// Must match MealType enum values from backend: soup, main_course, pasta, salad, dessert, breakfast, appetizer, etc.
const MEAL_TYPE_CONFIG = [
  { value: 'soup', label: 'Levesek', emoji: '🍲' },
  { value: 'main_course', label: 'Főételek', emoji: '🍽️' },
  { value: 'pasta', label: 'Tészták', emoji: '🍝' },
  { value: 'salad', label: 'Saláták', emoji: '🥗' },
  { value: 'dessert', label: 'Desszertek', emoji: '🍰' },
  { value: 'breakfast', label: 'Reggeli', emoji: '🍳' },
  { value: 'appetizer', label: 'Előételek', emoji: '🥗' },
]

export default function MealPool({
  meals = [],
  seasonalMeals = [],
  recentMeals = [],
  onMealClick,
}) {
  const { theme } = useTheme()
  const [search, setSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState(null) // null = show seasonal/recent
  const [seasonalPage, setSeasonalPage] = useState(0)
  const [recentPage, setRecentPage] = useState(0)
  const [categoryPage, setCategoryPage] = useState(0)

  // Filter meals based on search
  const filteredMeals = useMemo(() => {
    if (search.length < 2) return meals

    const searchLower = search.toLowerCase()
    return meals.filter(
      (meal) =>
        meal.name?.toLowerCase().includes(searchLower) ||
        meal.nev?.toLowerCase().includes(searchLower)
    )
  }, [meals, search])

  // Group meals by type for display
  const groupedMeals = useMemo(() => {
    const groups = {}
    MEAL_TYPE_CONFIG.forEach(({ value }) => {
      groups[value] = []
    })
    groups.other = []

    filteredMeals.forEach((meal) => {
      // API returns meal_type (snake_case), some places may use mealType (camelCase)
      const type = meal.meal_type || meal.mealType || 'other'
      if (groups[type]) {
        groups[type].push(meal)
      } else {
        groups.other.push(meal)
      }
    })
    return groups
  }, [filteredMeals])

  const isSearching = search.length >= 2

  // Get active category meals
  const activeCategoryMeals = activeCategory ? (groupedMeals[activeCategory] || []) : []
  const activeCategoryConfig = MEAL_TYPE_CONFIG.find(c => c.value === activeCategory)

  // Reset page when category changes
  const handleCategoryClick = (category) => {
    if (activeCategory === category) {
      setActiveCategory(null)
    } else {
      setActiveCategory(category)
      setCategoryPage(0)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <SearchInput
        value={search}
        onChange={setSearch}
        placeholder="Ételek keresése..."
      />

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto -mx-2 px-2">
        {isSearching ? (
          /* Search Results */
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: theme.colors.textSecondary }}>
                Találatok
              </span>
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: theme.colors.primaryLight, color: theme.colors.textPrimary }}
              >
                {filteredMeals.length}
              </span>
            </div>
            {filteredMeals.length > 0 ? (
              <div className="space-y-1.5">
                {filteredMeals.map((meal) => (
                  <DraggableMealCard
                    key={`search-${meal.id}`}
                    id={`search-${meal.id}`}
                    meal={meal}
                  />
                ))}
              </div>
            ) : (
              <div
                className="text-center py-6"
                style={{ background: theme.colors.cream, borderRadius: theme.borderRadius.md }}
              >
                <span className="text-2xl block mb-2">🔍</span>
                <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
                  Nincs találat: "{search}"
                </p>
              </div>
            )}
          </div>
        ) : activeCategory ? (
          /* Active Category View */
          <div>
            {/* Back button */}
            <button
              onClick={() => setActiveCategory(null)}
              className="flex items-center gap-2 text-sm mb-3 transition-colors"
              style={{ color: theme.colors.textPrimary }}
            >
              <span>←</span>
              <span>Vissza</span>
            </button>

            {/* Category header */}
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{activeCategoryConfig?.emoji}</span>
              <span className="font-medium" style={{ color: theme.colors.textPrimary }}>{activeCategoryConfig?.label}</span>
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: theme.colors.cream, color: theme.colors.textSecondary }}
              >
                {activeCategoryMeals.length}
              </span>
            </div>

            {/* Paginated list - 5 items per page */}
            <PaginatedMealList
              meals={activeCategoryMeals}
              page={categoryPage}
              onPageChange={setCategoryPage}
              idPrefix="category"
              theme={theme}
            />
          </div>
        ) : (
          /* Default View - Seasonal, Recent, Categories */
          <div className="space-y-4">
            {/* Szezonális ajánlatok */}
            {seasonalMeals.length > 0 && (
              <PaginatedSection
                title="Szezonális ajánlatok"
                emoji="🌸"
                meals={seasonalMeals}
                page={seasonalPage}
                onPageChange={setSeasonalPage}
                idPrefix="seasonal"
                defaultOpen={true}
                theme={theme}
              />
            )}

            {/* Legutóbb használt */}
            {recentMeals.length > 0 && (
              <PaginatedSection
                title="Legutóbb használt"
                emoji="🕐"
                meals={recentMeals}
                page={recentPage}
                onPageChange={setRecentPage}
                idPrefix="recent"
                defaultOpen={false}
                theme={theme}
              />
            )}

            {/* Category Buttons */}
            <div>
              <p className="text-xs font-medium mb-2" style={{ color: theme.colors.textSecondary }}>Kategóriák</p>
              <div className="grid grid-cols-2 gap-2">
                {MEAL_TYPE_CONFIG.map(({ value, label, emoji }) => {
                  const count = groupedMeals[value]?.length || 0
                  if (count === 0) return null
                  return (
                    <button
                      key={value}
                      onClick={() => handleCategoryClick(value)}
                      className="flex items-center gap-2 p-2 text-left transition-all hover:shadow-md"
                      style={{
                        background: theme.colors.cream,
                        border: `1px solid ${theme.colors.border}`,
                        borderRadius: theme.borderRadius.md,
                      }}
                    >
                      <span className="text-lg">{emoji}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate" style={{ color: theme.colors.textPrimary }}>{label}</p>
                        <p className="text-[10px]" style={{ color: theme.colors.textSecondary }}>{count} étel</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Empty State */}
            {filteredMeals.length === 0 && (
              <div
                className="text-center py-6"
                style={{ background: theme.colors.cream, borderRadius: theme.borderRadius.md }}
              >
                <span className="text-2xl block mb-2">🍽️</span>
                <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
                  Nincsenek ételek
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Paginated section with expand/collapse and pagination
function PaginatedSection({ title, emoji, meals, page, onPageChange, idPrefix, defaultOpen = true, theme }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const pageSize = 5
  const totalPages = Math.ceil(meals.length / pageSize)
  const startIdx = page * pageSize
  const visibleMeals = meals.slice(startIdx, startIdx + pageSize)
  const hasMore = page < totalPages - 1
  const hasPrev = page > 0

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-1.5 text-sm font-medium transition-colors"
        style={{ color: theme.colors.textPrimary }}
      >
        <span className="flex items-center gap-2">
          <span>{emoji}</span>
          {title}
        </span>
        <span className="flex items-center gap-2">
          <span
            className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: theme.colors.cream, color: theme.colors.textSecondary }}
          >
            {meals.length}
          </span>
          <span className={`transition-transform text-xs ${isOpen ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-1.5">
          {visibleMeals.map((meal) => (
            <DraggableMealCard
              key={`${idPrefix}-${meal.id}`}
              id={`${idPrefix}-${meal.id}`}
              meal={meal}
            />
          ))}

          {/* Pagination controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              {hasPrev && (
                <button
                  onClick={() => onPageChange(page - 1)}
                  className="w-8 h-8 flex items-center justify-center text-xs transition-colors"
                  style={{ background: theme.colors.cream, color: theme.colors.textPrimary, borderRadius: theme.borderRadius.sm }}
                >
                  ←
                </button>
              )}
              <span className="text-xs" style={{ color: theme.colors.textSecondary }}>
                {page + 1} / {totalPages}
              </span>
              {hasMore && (
                <button
                  onClick={() => onPageChange(page + 1)}
                  className="w-8 h-8 flex items-center justify-center text-xs font-medium transition-colors"
                  style={{ background: theme.colors.primary, color: 'white', borderRadius: theme.borderRadius.sm }}
                >
                  +
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Paginated meal list for category view
function PaginatedMealList({ meals, page, onPageChange, idPrefix, theme }) {
  const pageSize = 5
  const totalPages = Math.ceil(meals.length / pageSize)
  const startIdx = page * pageSize
  const visibleMeals = meals.slice(startIdx, startIdx + pageSize)
  const hasMore = page < totalPages - 1
  const hasPrev = page > 0

  return (
    <div className="space-y-1.5">
      {visibleMeals.map((meal) => (
        <DraggableMealCard
          key={`${idPrefix}-${meal.id}`}
          id={`${idPrefix}-${meal.id}`}
          meal={meal}
        />
      ))}

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          {hasPrev && (
            <button
              onClick={() => onPageChange(page - 1)}
              className="w-8 h-8 flex items-center justify-center text-xs transition-colors"
              style={{ background: theme.colors.cream, color: theme.colors.textPrimary, borderRadius: theme.borderRadius.sm }}
            >
              ←
            </button>
          )}
          <span className="text-xs" style={{ color: theme.colors.textSecondary }}>
            {page + 1} / {totalPages}
          </span>
          {hasMore && (
            <button
              onClick={() => onPageChange(page + 1)}
              className="w-8 h-8 flex items-center justify-center text-xs font-medium transition-colors"
              style={{ background: theme.colors.primary, color: 'white', borderRadius: theme.borderRadius.sm }}
            >
              +
            </button>
          )}
        </div>
      )}

      {meals.length === 0 && (
        <div
          className="text-center py-4"
          style={{ background: theme.colors.cream, borderRadius: theme.borderRadius.md }}
        >
          <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
            Nincs étel ebben a kategóriában
          </p>
        </div>
      )}
    </div>
  )
}
