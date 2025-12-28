import { useState, useEffect, useMemo, useCallback } from 'react'
import { useTheme } from '../context'
import { Button, Dialog } from '../components/ui'
import * as mealsApi from '../api/meals'
import {
  DndContext,
  DragOverlay,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
} from '@dnd-kit/core'

// Meal type labels in Hungarian
const MEAL_TYPE_LABELS = {
  soup: 'Leves',
  main_course: 'Főétel',
  pasta: 'Tészta',
  salad: 'Saláta',
  dessert: 'Desszert',
  breakfast: 'Reggeli',
  appetizer: 'Előétel',
  spread: 'Kenőke',
  beverage: 'Ital',
  condiment: 'Fűszer',
  dinner: 'Vacsora',
  meat: 'Hús',
  pastry: 'Péksütemény',
  vegan: 'Vegán',
}

// Cuisine labels in Hungarian
const CUISINE_LABELS = {
  hungarian: 'Magyar',
  italian: 'Olasz',
  french: 'Francia',
  indian: 'Indiai',
  middle_eastern: 'Közel-keleti',
  american: 'Amerikai',
  asian: 'Ázsiai',
  international: 'Nemzetközi',
  austrian: 'Osztrák',
  balkan: 'Balkáni',
  belgian: 'Belga',
  british: 'Brit',
  cuban: 'Kubai',
  german: 'Német',
  greek: 'Görög',
  mexican: 'Mexikói',
}

export default function MealsPage() {
  const { theme, themeName } = useTheme()

  // State
  const [meals, setMeals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterCuisine, setFilterCuisine] = useState('')
  const [selectedMeals, setSelectedMeals] = useState(new Set())
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState('asc')

  // View state
  const [viewMode, setViewMode] = useState('table') // 'table' | 'card'
  const [groupBy, setGroupBy] = useState('meal_type') // 'meal_type' | 'cuisine' | 'none'
  const [draggedMeal, setDraggedMeal] = useState(null)

  // Dialog states
  const [editMeal, setEditMeal] = useState(null)
  const [deleteMeal, setDeleteMeal] = useState(null)
  const [mergeMeals, setMergeMeals] = useState(null)
  const [showDuplicates, setShowDuplicates] = useState(false)

  // DnD sensors
  const mouseSensor = useSensor(MouseSensor, { activationConstraint: { distance: 8 } })
  const touchSensor = useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } })
  const sensors = useSensors(mouseSensor, touchSensor)

  // Load meals
  useEffect(() => {
    loadMeals()
  }, [])

  const loadMeals = async () => {
    setLoading(true)
    setError(null)
    try {
      // Request all meals (up to 500)
      const data = await mealsApi.getMeals({ limit: 500 })
      setMeals(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort meals
  const filteredMeals = useMemo(() => {
    let result = [...meals]

    // Search filter
    if (search) {
      const searchLower = search.toLowerCase()
      result = result.filter(m =>
        m.name?.toLowerCase().includes(searchLower) ||
        m.nev?.toLowerCase().includes(searchLower)
      )
    }

    // Type filter
    if (filterType) {
      result = result.filter(m => m.meal_type === filterType)
    }

    // Cuisine filter
    if (filterCuisine) {
      result = result.filter(m => m.cuisine === filterCuisine)
    }

    // Sort
    result.sort((a, b) => {
      let aVal = a[sortBy] || ''
      let bVal = b[sortBy] || ''
      if (typeof aVal === 'string') aVal = aVal.toLowerCase()
      if (typeof bVal === 'string') bVal = bVal.toLowerCase()
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })

    return result
  }, [meals, search, filterType, filterCuisine, sortBy, sortOrder])

  // Find duplicates (similar names)
  const duplicates = useMemo(() => {
    const groups = {}
    meals.forEach(meal => {
      const key = (meal.nev || meal.name || '').toLowerCase().trim()
      if (!groups[key]) groups[key] = []
      groups[key].push(meal)
    })
    return Object.values(groups).filter(g => g.length > 1)
  }, [meals])

  // Get unique types and cuisines for filters
  const mealTypes = useMemo(() =>
    [...new Set(meals.map(m => m.meal_type).filter(Boolean))].sort(),
    [meals]
  )
  const cuisines = useMemo(() =>
    [...new Set(meals.map(m => m.cuisine).filter(Boolean))].sort(),
    [meals]
  )

  // Group meals for card view
  const groupedMeals = useMemo(() => {
    if (groupBy === 'none') {
      return { 'Összes étel': { key: 'all', meals: filteredMeals } }
    }

    const groups = {}
    const labels = groupBy === 'meal_type' ? MEAL_TYPE_LABELS : CUISINE_LABELS
    const allKeys = groupBy === 'meal_type' ? Object.keys(MEAL_TYPE_LABELS) : Object.keys(CUISINE_LABELS)

    // Initialize all groups
    allKeys.forEach(key => {
      groups[key] = []
    })
    groups['_uncategorized'] = []

    // Distribute meals into groups
    filteredMeals.forEach(meal => {
      const key = meal[groupBy]
      if (key && groups[key]) {
        groups[key].push(meal)
      } else {
        groups['_uncategorized'].push(meal)
      }
    })

    // Convert to object with labels, include empty groups for drop targets
    const result = {}
    allKeys.forEach(key => {
      result[labels[key] || key] = { key, meals: groups[key] }
    })
    if (groups['_uncategorized'].length > 0) {
      result['Kategorizálatlan'] = { key: null, meals: groups['_uncategorized'] }
    }

    return result
  }, [filteredMeals, groupBy])

  // Handlers
  const handleSelectAll = () => {
    if (selectedMeals.size === filteredMeals.length) {
      setSelectedMeals(new Set())
    } else {
      setSelectedMeals(new Set(filteredMeals.map(m => m.id)))
    }
  }

  const handleSelectMeal = (id) => {
    const newSelected = new Set(selectedMeals)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedMeals(newSelected)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteMeal) return
    try {
      await mealsApi.deleteMeal(deleteMeal.id)
      setMeals(prev => prev.filter(m => m.id !== deleteMeal.id))
      setDeleteMeal(null)
      setSelectedMeals(prev => {
        const newSet = new Set(prev)
        newSet.delete(deleteMeal.id)
        return newSet
      })
    } catch (err) {
      alert('Hiba: ' + err.message)
    }
  }

  const handleBulkDelete = async () => {
    if (selectedMeals.size === 0) return
    if (!confirm(`Biztosan törölni szeretnéd a kiválasztott ${selectedMeals.size} ételt?`)) return

    try {
      for (const id of selectedMeals) {
        await mealsApi.deleteMeal(id)
      }
      setMeals(prev => prev.filter(m => !selectedMeals.has(m.id)))
      setSelectedMeals(new Set())
    } catch (err) {
      alert('Hiba: ' + err.message)
      loadMeals()
    }
  }

  const handleEditSave = async (data) => {
    if (!editMeal) return
    try {
      const updated = await mealsApi.updateMeal(editMeal.id, data)
      setMeals(prev => prev.map(m => m.id === editMeal.id ? { ...m, ...updated } : m))
      setEditMeal(null)
    } catch (err) {
      alert('Hiba: ' + err.message)
    }
  }

  const handleMergeConfirm = async (mergedData, targetId, sourceIds) => {
    try {
      // Update target meal with merged data
      await mealsApi.updateMeal(targetId, mergedData)

      // Delete source meals
      for (const sourceId of sourceIds) {
        await mealsApi.deleteMeal(sourceId)
      }

      // Update local state
      setMeals(prev => {
        const updated = prev.filter(m => !sourceIds.includes(m.id))
        return updated.map(m => m.id === targetId ? { ...m, ...mergedData } : m)
      })
      setMergeMeals(null)
      setSelectedMeals(new Set())
    } catch (err) {
      alert('Hiba: ' + err.message)
      loadMeals()
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
  }

  const startMerge = () => {
    const selected = meals.filter(m => selectedMeals.has(m.id))
    if (selected.length < 2) {
      alert('Legalább 2 ételt válassz ki az egyesítéshez!')
      return
    }
    setMergeMeals(selected)
  }

  // Drag and drop handlers for card view
  const handleDragStart = (event) => {
    const { active } = event
    const meal = meals.find(m => m.id === active.id)
    if (meal) {
      setDraggedMeal(meal)
    }
  }

  const handleDragEnd = useCallback(async (event) => {
    const { active, over } = event
    setDraggedMeal(null)

    if (!over || !active) return

    const mealId = active.id
    const targetGroup = over.id // This is the group key (e.g., 'soup', 'hungarian')

    // Find the meal
    const meal = meals.find(m => m.id === mealId)
    if (!meal) return

    // Skip if dropping on same group or uncategorized
    if (targetGroup === '_uncategorized') return
    if (meal[groupBy] === targetGroup) return

    // Optimistic update
    setMeals(prev => prev.map(m =>
      m.id === mealId ? { ...m, [groupBy]: targetGroup } : m
    ))

    // API call
    try {
      await mealsApi.updateMeal(mealId, { [groupBy]: targetGroup })
    } catch (err) {
      alert('Hiba: ' + err.message)
      loadMeals() // Revert on error
    }
  }, [meals, groupBy, loadMeals])

  const handleDragCancel = () => {
    setDraggedMeal(null)
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center" style={{ background: theme.colors.background }}>
        <div className="text-center">
          <div className="text-4xl mb-4">🍽️</div>
          <p style={{ color: theme.colors.textSecondary }}>Ételek betöltése...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: theme.colors.background }}>
      {/* Header */}
      <header
        className="sticky top-0 z-10 border-b"
        style={{ background: theme.colors.cardBackground, borderColor: theme.colors.border }}
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <a
                href="/"
                className="text-2xl font-medium"
                style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif, textDecoration: 'none' }}
              >
                Carmy
              </a>
              <span style={{ color: theme.colors.textSecondary }}>/</span>
              <h1
                className="text-xl font-medium"
                style={{ color: theme.colors.textPrimary, fontFamily: theme.fontSerif }}
              >
                Ételek kezelése
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="px-3 py-1 text-sm rounded-full"
                style={{ background: theme.colors.primaryLight, color: theme.colors.textPrimary }}
              >
                {meals.length} étel
              </span>
              {duplicates.length > 0 && (
                <button
                  onClick={() => setShowDuplicates(true)}
                  className="px-3 py-1 text-sm rounded-full"
                  style={{ background: `${theme.colors.danger}20`, color: theme.colors.danger }}
                >
                  {duplicates.length} duplikált
                </button>
              )}
            </div>
          </div>

          {/* Search and filters */}
          <div className="flex flex-wrap gap-3">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Keresés..."
              className="flex-1 min-w-[200px] px-4 py-2 text-sm"
              style={{
                background: theme.colors.cream,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: theme.colors.textPrimary,
              }}
            />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 text-sm"
              style={{
                background: theme.colors.cream,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: theme.colors.textPrimary,
              }}
            >
              <option value="">Minden típus</option>
              {mealTypes.map(type => (
                <option key={type} value={type}>{MEAL_TYPE_LABELS[type] || type}</option>
              ))}
            </select>
            <select
              value={filterCuisine}
              onChange={(e) => setFilterCuisine(e.target.value)}
              className="px-3 py-2 text-sm"
              style={{
                background: theme.colors.cream,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: theme.colors.textPrimary,
              }}
            >
              <option value="">Minden konyha</option>
              {cuisines.map(cuisine => (
                <option key={cuisine} value={cuisine}>{CUISINE_LABELS[cuisine] || cuisine}</option>
              ))}
            </select>

            {/* View toggle */}
            <div
              className="flex rounded-lg overflow-hidden"
              style={{ border: `1px solid ${theme.colors.border}` }}
            >
              <button
                onClick={() => setViewMode('table')}
                className="px-3 py-2 text-sm"
                style={{
                  background: viewMode === 'table' ? theme.colors.primary : theme.colors.cream,
                  color: viewMode === 'table' ? theme.colors.white : theme.colors.textPrimary,
                }}
              >
                ☰ Táblázat
              </button>
              <button
                onClick={() => setViewMode('card')}
                className="px-3 py-2 text-sm"
                style={{
                  background: viewMode === 'card' ? theme.colors.primary : theme.colors.cream,
                  color: viewMode === 'card' ? theme.colors.white : theme.colors.textPrimary,
                }}
              >
                ▦ Kártyák
              </button>
            </div>

            {/* Group by (only in card view) */}
            {viewMode === 'card' && (
              <select
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
                className="px-3 py-2 text-sm"
                style={{
                  background: theme.colors.cream,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: theme.borderRadius.sm,
                  color: theme.colors.textPrimary,
                }}
              >
                <option value="meal_type">Csoportosítás: Típus</option>
                <option value="cuisine">Csoportosítás: Konyha</option>
                <option value="none">Nincs csoportosítás</option>
              </select>
            )}
          </div>
        </div>
      </header>

      {/* Actions bar */}
      {selectedMeals.size > 0 && (
        <div
          className="sticky top-[120px] z-10 border-b"
          style={{ background: theme.colors.primaryLight, borderColor: theme.colors.border }}
        >
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <span className="text-sm font-medium" style={{ color: theme.colors.textPrimary }}>
              {selectedMeals.size} kiválasztva
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => setSelectedMeals(new Set())}>
                Kijelölés törlése
              </Button>
              {selectedMeals.size >= 2 && (
                <Button size="sm" variant="secondary" onClick={startMerge}>
                  Egyesítés
                </Button>
              )}
              <Button size="sm" variant="danger" onClick={handleBulkDelete}>
                Törlés ({selectedMeals.size})
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        {error && (
          <div
            className="mb-4 p-4 rounded-lg"
            style={{ background: `${theme.colors.danger}20`, color: theme.colors.danger }}
          >
            Hiba: {error}
            <button onClick={loadMeals} className="ml-2 underline">Újrapróbálás</button>
          </div>
        )}

        {/* Table View */}
        {viewMode === 'table' && (
          <div
            className="rounded-lg overflow-hidden border"
            style={{ background: theme.colors.cardBackground, borderColor: theme.colors.border }}
          >
            <table className="w-full">
              <thead>
                <tr style={{ background: theme.colors.cream }}>
                  <th className="p-3 text-left w-10">
                    <input
                      type="checkbox"
                      checked={selectedMeals.size === filteredMeals.length && filteredMeals.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th
                    className="p-3 text-left cursor-pointer select-none"
                    style={{ color: theme.colors.textSecondary }}
                    onClick={() => handleSort('nev')}
                  >
                    Név {sortBy === 'nev' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="p-3 text-left cursor-pointer select-none"
                    style={{ color: theme.colors.textSecondary }}
                    onClick={() => handleSort('meal_type')}
                  >
                    Típus {sortBy === 'meal_type' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="p-3 text-left cursor-pointer select-none"
                    style={{ color: theme.colors.textSecondary }}
                    onClick={() => handleSort('cuisine')}
                  >
                    Konyha {sortBy === 'cuisine' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="p-3 text-left" style={{ color: theme.colors.textSecondary }}>
                    Adagok
                  </th>
                  <th className="p-3 text-right" style={{ color: theme.colors.textSecondary }}>
                    Műveletek
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredMeals.map((meal) => (
                  <tr
                    key={meal.id}
                    className="border-t transition-colors hover:bg-opacity-50"
                    style={{
                      borderColor: theme.colors.borderLight,
                      background: selectedMeals.has(meal.id) ? `${theme.colors.primary}10` : 'transparent',
                    }}
                  >
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selectedMeals.has(meal.id)}
                        onChange={() => handleSelectMeal(meal.id)}
                      />
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{meal.emoji || '🍽️'}</span>
                        <div>
                          <p className="font-medium" style={{ color: theme.colors.textPrimary }}>
                            {meal.nev || meal.name}
                          </p>
                          {meal.nev && meal.name && meal.nev !== meal.name && (
                            <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
                              {meal.name}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="p-3">
                      <span
                        className="px-2 py-1 text-xs rounded-full"
                        style={{ background: theme.colors.cream, color: theme.colors.textSecondary }}
                      >
                        {MEAL_TYPE_LABELS[meal.meal_type] || meal.meal_type || '-'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span style={{ color: theme.colors.textSecondary }}>
                        {CUISINE_LABELS[meal.cuisine] || meal.cuisine || '-'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span style={{ color: theme.colors.textSecondary }}>
                        {meal.default_portions || meal.servings || 1}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => setEditMeal(meal)}
                          className="px-2 py-1 text-xs rounded"
                          style={{ background: theme.colors.cream, color: theme.colors.textPrimary }}
                        >
                          Szerkesztés
                        </button>
                        <button
                          onClick={() => setDeleteMeal(meal)}
                          className="px-2 py-1 text-xs rounded"
                          style={{ background: `${theme.colors.danger}20`, color: theme.colors.danger }}
                        >
                          Törlés
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredMeals.length === 0 && (
              <div className="p-8 text-center" style={{ color: theme.colors.textSecondary }}>
                Nincs találat
              </div>
            )}
          </div>
        )}

        {/* Card View with Drag and Drop */}
        {viewMode === 'card' && (
          <DndContext
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragCancel={handleDragCancel}
          >
            {groupBy !== 'none' && (
              <p className="text-sm mb-4" style={{ color: theme.colors.textSecondary }}>
                Húzd az ételeket a csoportok között a {groupBy === 'meal_type' ? 'típus' : 'konyha'} módosításához
              </p>
            )}

            <div className="space-y-6">
              {Object.entries(groupedMeals).map(([label, group]) => (
                <MealGroup
                  key={label}
                  label={label}
                  groupKey={group.key}
                  meals={group.meals}
                  groupBy={groupBy}
                  selectedMeals={selectedMeals}
                  onSelectMeal={handleSelectMeal}
                  onEditMeal={setEditMeal}
                  onDeleteMeal={setDeleteMeal}
                />
              ))}
            </div>

            {filteredMeals.length === 0 && (
              <div className="p-8 text-center" style={{ color: theme.colors.textSecondary }}>
                Nincs találat
              </div>
            )}

            {/* Drag Overlay */}
            <DragOverlay dropAnimation={null}>
              {draggedMeal && <DraggedMealCard meal={draggedMeal} />}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {/* Edit Dialog */}
      <EditMealDialog
        meal={editMeal}
        onClose={() => setEditMeal(null)}
        onSave={handleEditSave}
        mealTypes={mealTypes}
        cuisines={cuisines}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        isOpen={!!deleteMeal}
        onClose={() => setDeleteMeal(null)}
        title="Étel törlése"
      >
        <p style={{ color: theme.colors.textSecondary }}>
          Biztosan törölni szeretnéd a(z) <strong>{deleteMeal?.nev || deleteMeal?.name}</strong> ételt?
        </p>
        <div className="flex gap-3 mt-6">
          <Button variant="secondary" onClick={() => setDeleteMeal(null)}>Mégse</Button>
          <Button variant="danger" onClick={handleDeleteConfirm}>Törlés</Button>
        </div>
      </Dialog>

      {/* Merge Dialog */}
      <MergeMealsDialog
        meals={mergeMeals}
        onClose={() => setMergeMeals(null)}
        onConfirm={handleMergeConfirm}
      />

      {/* Duplicates Dialog */}
      <DuplicatesDialog
        isOpen={showDuplicates}
        onClose={() => setShowDuplicates(false)}
        duplicates={duplicates}
        onMerge={(group) => {
          setMergeMeals(group)
          setShowDuplicates(false)
        }}
      />
    </div>
  )
}

// Meal Group Component (droppable area)
function MealGroup({ label, groupKey, meals, groupBy, selectedMeals, onSelectMeal, onEditMeal, onDeleteMeal }) {
  const { theme } = useTheme()
  const { setNodeRef, isOver } = useDroppable({
    id: groupKey || '_uncategorized',
  })

  return (
    <div
      ref={setNodeRef}
      className="rounded-lg border p-4 transition-all"
      style={{
        background: isOver ? `${theme.colors.primary}10` : theme.colors.cardBackground,
        borderColor: isOver ? theme.colors.primary : theme.colors.border,
        borderWidth: isOver ? '2px' : '1px',
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium" style={{ color: theme.colors.textPrimary }}>
          {label}
        </h3>
        <span
          className="px-2 py-1 text-xs rounded-full"
          style={{ background: theme.colors.cream, color: theme.colors.textSecondary }}
        >
          {meals.length} étel
        </span>
      </div>

      {meals.length === 0 ? (
        <div
          className="p-6 text-center border-2 border-dashed rounded-lg"
          style={{ borderColor: theme.colors.border, color: theme.colors.textSecondary }}
        >
          Húzz ide ételeket
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {meals.map(meal => (
            <DraggableMealCard
              key={meal.id}
              meal={meal}
              isSelected={selectedMeals.has(meal.id)}
              onSelect={() => onSelectMeal(meal.id)}
              onEdit={() => onEditMeal(meal)}
              onDelete={() => onDeleteMeal(meal)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Draggable Meal Card for Card View
function DraggableMealCard({ meal, isSelected, onSelect, onEdit, onDelete }) {
  const { theme } = useTheme()
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: meal.id,
  })

  const style = transform
    ? {
        transform: `translate(${transform.x}px, ${transform.y}px)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : {}

  return (
    <div
      ref={setNodeRef}
      style={{
        ...style,
        background: isSelected ? `${theme.colors.primary}15` : theme.colors.cream,
        border: `1px solid ${isSelected ? theme.colors.primary : theme.colors.border}`,
        borderRadius: theme.borderRadius.md,
      }}
      className="p-3 cursor-grab active:cursor-grabbing"
      {...listeners}
      {...attributes}
    >
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          onClick={(e) => e.stopPropagation()}
          className="mt-1"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xl">{meal.emoji || '🍽️'}</span>
            <p
              className="font-medium text-sm truncate"
              style={{ color: theme.colors.textPrimary }}
              title={meal.nev || meal.name}
            >
              {meal.nev || meal.name}
            </p>
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {meal.meal_type && (
              <span
                className="px-1.5 py-0.5 text-xs rounded"
                style={{ background: theme.colors.primaryLight, color: theme.colors.textSecondary }}
              >
                {MEAL_TYPE_LABELS[meal.meal_type] || meal.meal_type}
              </span>
            )}
            {meal.cuisine && (
              <span
                className="px-1.5 py-0.5 text-xs rounded"
                style={{ background: theme.colors.secondaryLight, color: theme.colors.textSecondary }}
              >
                {CUISINE_LABELS[meal.cuisine] || meal.cuisine}
              </span>
            )}
          </div>
          <div className="flex gap-1 mt-2">
            <button
              onClick={(e) => { e.stopPropagation(); onEdit(); }}
              className="px-2 py-1 text-xs rounded"
              style={{ background: theme.colors.cardBackground, color: theme.colors.textSecondary }}
            >
              Szerk.
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="px-2 py-1 text-xs rounded"
              style={{ background: `${theme.colors.danger}15`, color: theme.colors.danger }}
            >
              Törlés
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Drag overlay card (shown while dragging)
function DraggedMealCard({ meal }) {
  const { theme } = useTheme()

  return (
    <div
      className="p-3 shadow-lg"
      style={{
        background: theme.colors.cardBackground,
        border: `2px solid ${theme.colors.primary}`,
        borderRadius: theme.borderRadius.md,
        width: '200px',
      }}
    >
      <div className="flex items-center gap-2">
        <span className="text-xl">{meal.emoji || '🍽️'}</span>
        <p className="font-medium text-sm" style={{ color: theme.colors.textPrimary }}>
          {meal.nev || meal.name}
        </p>
      </div>
    </div>
  )
}

// Edit Meal Dialog Component
function EditMealDialog({ meal, onClose, onSave, mealTypes, cuisines }) {
  const { theme } = useTheme()
  const [form, setForm] = useState({})

  useEffect(() => {
    if (meal) {
      setForm({
        nev: meal.nev || '',
        name: meal.name || '',
        meal_type: meal.meal_type || '',
        cuisine: meal.cuisine || '',
        default_portions: meal.default_portions || meal.servings || 1,
        is_vegetarian: meal.is_vegetarian || false,
        has_meat: meal.has_meat || false,
      })
    }
  }, [meal])

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(form)
  }

  if (!meal) return null

  return (
    <Dialog isOpen={!!meal} onClose={onClose} title="Étel szerkesztése">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm mb-1" style={{ color: theme.colors.textSecondary }}>
            Magyar név
          </label>
          <input
            type="text"
            value={form.nev || ''}
            onChange={(e) => setForm(f => ({ ...f, nev: e.target.value }))}
            className="w-full px-3 py-2 text-sm"
            style={{
              background: theme.colors.cream,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius.sm,
              color: theme.colors.textPrimary,
            }}
          />
        </div>
        <div>
          <label className="block text-sm mb-1" style={{ color: theme.colors.textSecondary }}>
            Angol név
          </label>
          <input
            type="text"
            value={form.name || ''}
            onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full px-3 py-2 text-sm"
            style={{
              background: theme.colors.cream,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius.sm,
              color: theme.colors.textPrimary,
            }}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: theme.colors.textSecondary }}>
              Típus
            </label>
            <select
              value={form.meal_type || ''}
              onChange={(e) => setForm(f => ({ ...f, meal_type: e.target.value }))}
              className="w-full px-3 py-2 text-sm"
              style={{
                background: theme.colors.cream,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: theme.colors.textPrimary,
              }}
            >
              <option value="">Nincs</option>
              {mealTypes.map(type => (
                <option key={type} value={type}>{MEAL_TYPE_LABELS[type] || type}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: theme.colors.textSecondary }}>
              Konyha
            </label>
            <select
              value={form.cuisine || ''}
              onChange={(e) => setForm(f => ({ ...f, cuisine: e.target.value }))}
              className="w-full px-3 py-2 text-sm"
              style={{
                background: theme.colors.cream,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.sm,
                color: theme.colors.textPrimary,
              }}
            >
              <option value="">Nincs</option>
              {cuisines.map(cuisine => (
                <option key={cuisine} value={cuisine}>{CUISINE_LABELS[cuisine] || cuisine}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm mb-1" style={{ color: theme.colors.textSecondary }}>
            Alapértelmezett adagok
          </label>
          <input
            type="number"
            min="1"
            value={form.default_portions || 1}
            onChange={(e) => setForm(f => ({ ...f, default_portions: parseInt(e.target.value) || 1 }))}
            className="w-full px-3 py-2 text-sm"
            style={{
              background: theme.colors.cream,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius.sm,
              color: theme.colors.textPrimary,
            }}
          />
        </div>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm" style={{ color: theme.colors.textSecondary }}>
            <input
              type="checkbox"
              checked={form.is_vegetarian || false}
              onChange={(e) => setForm(f => ({ ...f, is_vegetarian: e.target.checked }))}
            />
            Vegetáriánus
          </label>
          <label className="flex items-center gap-2 text-sm" style={{ color: theme.colors.textSecondary }}>
            <input
              type="checkbox"
              checked={form.has_meat || false}
              onChange={(e) => setForm(f => ({ ...f, has_meat: e.target.checked }))}
            />
            Húsos
          </label>
        </div>
        <div className="flex gap-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>Mégse</Button>
          <Button type="submit" variant="primary">Mentés</Button>
        </div>
      </form>
    </Dialog>
  )
}

// Field labels for merge dialog
const FIELD_LABELS = {
  nev: 'Magyar név',
  name: 'Angol név',
  emoji: 'Emoji',
  meal_type: 'Típus',
  cuisine: 'Konyha',
  default_portions: 'Adagok',
  is_vegetarian: 'Vegetáriánus',
  has_meat: 'Húsos',
}

// Fields that can be merged
const MERGEABLE_FIELDS = ['nev', 'name', 'emoji', 'meal_type', 'cuisine', 'default_portions', 'is_vegetarian', 'has_meat']

// Merge Meals Dialog Component - Field-by-field selection
function MergeMealsDialog({ meals, onClose, onConfirm }) {
  const { theme } = useTheme()
  const [targetId, setTargetId] = useState(null)
  const [selectedValues, setSelectedValues] = useState({})

  // Initialize target and selected values when meals change
  useEffect(() => {
    if (meals?.length) {
      setTargetId(meals[0].id)
      // Initialize with first meal's values
      const initial = {}
      MERGEABLE_FIELDS.forEach(field => {
        initial[field] = { value: meals[0][field], sourceId: meals[0].id }
      })
      setSelectedValues(initial)
    }
  }, [meals])

  if (!meals || meals.length < 2) return null

  const sourceIds = meals.filter(m => m.id !== targetId).map(m => m.id)

  // Get unique values for a field from all meals
  const getFieldOptions = (field) => {
    const options = []
    const seen = new Set()
    meals.forEach(meal => {
      const value = meal[field]
      const key = typeof value === 'boolean' ? String(value) : (value || '')
      if (!seen.has(key)) {
        seen.add(key)
        options.push({ value, sourceId: meal.id, mealName: meal.nev || meal.name })
      }
    })
    return options
  }

  // Format value for display
  const formatValue = (field, value) => {
    if (value === null || value === undefined || value === '') return '(üres)'
    if (typeof value === 'boolean') return value ? 'Igen' : 'Nem'
    if (field === 'meal_type') return MEAL_TYPE_LABELS[value] || value
    if (field === 'cuisine') return CUISINE_LABELS[value] || value
    return String(value)
  }

  // Handle field value selection
  const handleSelectValue = (field, value, sourceId) => {
    setSelectedValues(prev => ({
      ...prev,
      [field]: { value, sourceId }
    }))
  }

  // Build merged data object
  const buildMergedData = () => {
    const data = {}
    MERGEABLE_FIELDS.forEach(field => {
      if (selectedValues[field]?.value !== undefined) {
        data[field] = selectedValues[field].value
      }
    })
    return data
  }

  const handleConfirm = () => {
    const mergedData = buildMergedData()
    onConfirm(mergedData, targetId, sourceIds)
  }

  return (
    <Dialog isOpen={!!meals} onClose={onClose} title="Ételek egyesítése">
      {/* Step 1: Select target meal */}
      <div className="mb-6">
        <h3 className="text-sm font-medium mb-2" style={{ color: theme.colors.textPrimary }}>
          1. Válaszd ki a megmaradó ételt (ID)
        </h3>
        <div className="flex flex-wrap gap-2">
          {meals.map(meal => (
            <button
              key={meal.id}
              onClick={() => setTargetId(meal.id)}
              className="px-3 py-2 rounded-lg text-sm"
              style={{
                background: targetId === meal.id ? theme.colors.primary : theme.colors.cream,
                color: targetId === meal.id ? theme.colors.white : theme.colors.textPrimary,
                border: `2px solid ${targetId === meal.id ? theme.colors.primary : theme.colors.border}`,
              }}
            >
              {meal.emoji || '🍽️'} {meal.nev || meal.name}
              <span className="opacity-60 ml-1">(#{meal.id})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Step 2: Field-by-field selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium mb-3" style={{ color: theme.colors.textPrimary }}>
          2. Válaszd ki az adatokat minden mezőhöz
        </h3>
        <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
          {MERGEABLE_FIELDS.map(field => {
            const options = getFieldOptions(field)
            const currentSelection = selectedValues[field]

            // Skip if all values are the same
            if (options.length <= 1) {
              return (
                <div key={field} className="opacity-50">
                  <label className="block text-xs mb-1" style={{ color: theme.colors.textSecondary }}>
                    {FIELD_LABELS[field]}
                  </label>
                  <div
                    className="px-3 py-2 rounded text-sm"
                    style={{ background: theme.colors.cream, color: theme.colors.textPrimary }}
                  >
                    {formatValue(field, options[0]?.value)} <span className="opacity-50">(egyezik)</span>
                  </div>
                </div>
              )
            }

            return (
              <div key={field}>
                <label className="block text-xs mb-1" style={{ color: theme.colors.textSecondary }}>
                  {FIELD_LABELS[field]}
                </label>
                <div className="flex flex-wrap gap-2">
                  {options.map((opt, idx) => {
                    const isSelected = currentSelection?.sourceId === opt.sourceId &&
                                       currentSelection?.value === opt.value
                    return (
                      <button
                        key={idx}
                        onClick={() => handleSelectValue(field, opt.value, opt.sourceId)}
                        className="px-3 py-2 rounded text-sm text-left"
                        style={{
                          background: isSelected ? `${theme.colors.primary}20` : theme.colors.cream,
                          border: `2px solid ${isSelected ? theme.colors.primary : 'transparent'}`,
                          color: theme.colors.textPrimary,
                        }}
                      >
                        <span className="font-medium">{formatValue(field, opt.value)}</span>
                        <span className="block text-xs opacity-60">{opt.mealName}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary */}
      <div
        className="p-3 rounded-lg mb-4"
        style={{ background: theme.colors.cream }}
      >
        <p className="text-sm font-medium mb-2" style={{ color: theme.colors.textPrimary }}>
          Összesítés:
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {MERGEABLE_FIELDS.map(field => (
            <div key={field}>
              <span style={{ color: theme.colors.textSecondary }}>{FIELD_LABELS[field]}: </span>
              <span style={{ color: theme.colors.textPrimary }}>
                {formatValue(field, selectedValues[field]?.value)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Warning */}
      <div
        className="p-3 rounded-lg mb-4"
        style={{ background: `${theme.colors.danger}10` }}
      >
        <p className="text-sm" style={{ color: theme.colors.danger }}>
          <strong>Figyelem:</strong> {sourceIds.length} étel törlésre kerül az egyesítés után.
        </p>
      </div>

      <div className="flex gap-3">
        <Button variant="secondary" onClick={onClose}>Mégse</Button>
        <Button variant="primary" onClick={handleConfirm}>
          Egyesítés
        </Button>
      </div>
    </Dialog>
  )
}

// Duplicates Dialog Component
function DuplicatesDialog({ isOpen, onClose, duplicates, onMerge }) {
  const { theme } = useTheme()

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="Duplikált ételek">
      <div className="max-h-96 overflow-y-auto space-y-4">
        {duplicates.map((group, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg"
            style={{ background: theme.colors.cream }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium" style={{ color: theme.colors.textPrimary }}>
                "{group[0].nev || group[0].name}" ({group.length} db)
              </span>
              <button
                onClick={() => onMerge(group)}
                className="px-2 py-1 text-xs rounded"
                style={{ background: theme.colors.primary, color: theme.colors.white }}
              >
                Egyesítés
              </button>
            </div>
            <div className="space-y-1">
              {group.map(meal => (
                <div key={meal.id} className="text-sm flex items-center gap-2">
                  <span>{meal.emoji || '🍽️'}</span>
                  <span style={{ color: theme.colors.textSecondary }}>
                    ID: {meal.id} - {MEAL_TYPE_LABELS[meal.meal_type] || meal.meal_type || 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {duplicates.length === 0 && (
          <p style={{ color: theme.colors.textSecondary }}>Nincsenek duplikált ételek!</p>
        )}
      </div>
      <div className="mt-4">
        <Button variant="secondary" onClick={onClose}>Bezárás</Button>
      </div>
    </Dialog>
  )
}
