import { BrowserRouter, Routes, Route, useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import {
  DndContext,
  DragOverlay,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { BoardLayout, WeekGrid, DragOverlayContent } from './components/board'
import { Sidebar } from './components/layout'
import { MealPool } from './components/pool'
import { Button, PortionDialog, LoadingPage, ErrorPage, ThemeSwitcher } from './components/ui'
import { MealsPage } from './pages'
import { useBoard } from './hooks'
import { plans } from './api'
import { ThemeProvider } from './context'

// Get current ISO week
function getCurrentWeek() {
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 1)
  const diff = now - start + ((start.getTimezoneOffset() - now.getTimezoneOffset()) * 60000)
  const oneWeek = 604800000
  const week = Math.ceil((diff / oneWeek + start.getDay() + 1) / 7)
  return { year: now.getFullYear(), week }
}

// Format date range for display - Hungarian format
function formatDateRange(startDate, endDate) {
  if (!startDate) return ''
  const start = new Date(startDate)
  const end = endDate ? new Date(endDate) : new Date(start.getTime() + 6 * 24 * 60 * 60 * 1000)
  const options = { month: 'short', day: 'numeric' }
  return `${start.toLocaleDateString('hu-HU', options)} – ${end.toLocaleDateString('hu-HU', options)}, ${start.getFullYear()}`
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<BoardPage />} />
          <Route path="/board" element={<BoardPage />} />
          <Route path="/board/week/:year/:week" element={<BoardPage />} />
          <Route path="/meals" element={<MealsPage />} />
        </Routes>
        <ThemeSwitcher />
      </BrowserRouter>
    </ThemeProvider>
  )
}

function BoardPage() {
  const params = useParams()
  const navigate = useNavigate()

  const current = getCurrentWeek()
  const year = params.year ? parseInt(params.year) : current.year
  const week = params.week ? parseInt(params.week) : current.week

  // Fetch board data from API
  const { data: boardData, loading, error, refetch, assignMeal, removeMeal } = useBoard(year, week)

  // Local state for optimistic updates
  const [localDays, setLocalDays] = useState(null)

  // Sync local state with API data
  useEffect(() => {
    if (boardData?.days) {
      setLocalDays(boardData.days)
    }
  }, [boardData])

  // Drag state
  const [activeMeal, setActiveMeal] = useState(null)

  // Portion dialog state
  const [portionDialog, setPortionDialog] = useState({
    isOpen: false,
    meal: null,
    dayIndex: null,
    slotType: null,
  })

  // Configure sensors for drag detection
  const mouseSensor = useSensor(MouseSensor, {
    activationConstraint: {
      distance: 8,
    },
  })
  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: {
      delay: 200,
      tolerance: 5,
    },
  })
  const sensors = useSensors(mouseSensor, touchSensor)

  const handlePrev = () => {
    let newWeek = week - 1
    let newYear = year
    if (newWeek < 1) {
      newWeek = 52
      newYear -= 1
    }
    navigate(`/board/week/${newYear}/${newWeek}`)
  }

  const handleNext = () => {
    let newWeek = week + 1
    let newYear = year
    if (newWeek > 52) {
      newWeek = 1
      newYear += 1
    }
    navigate(`/board/week/${newYear}/${newWeek}`)
  }

  const handleToday = () => {
    // Today is Dec 27, 2025 = Week 52
    navigate('/board/week/2025/52')
  }

  // Drag handlers
  const handleDragStart = (event) => {
    const { active } = event
    const meal = active.data.current?.meal
    if (meal) {
      setActiveMeal(meal)
    }
  }

  const handleDragEnd = (event) => {
    const { active, over } = event

    if (over && active.data.current?.meal) {
      const meal = active.data.current.meal
      const [dayIndex, slotType] = over.id.split('-')
      const dayIdx = parseInt(dayIndex)

      // Check if meal has multiple portions
      if ((meal.portions || 1) > 1) {
        setPortionDialog({
          isOpen: true,
          meal,
          dayIndex: dayIdx,
          slotType,
        })
      } else {
        handleAssignMeal(meal, dayIdx, slotType, false, 1)
      }
    }

    setActiveMeal(null)
  }

  const handleDragCancel = () => {
    setActiveMeal(null)
  }

  // Assign meal to slot via API
  const handleAssignMeal = useCallback(
    async (meal, dayIndex, slotType, createChain, chainDays) => {
      // Optimistic update
      setLocalDays((prev) => {
        if (!prev) return prev
        const newDays = [...prev]

        if (createChain && chainDays > 1) {
          for (let i = 0; i < chainDays && dayIndex + i < 7; i++) {
            const isFirst = i === 0
            const isLast = i === chainDays - 1
            const day = { ...newDays[dayIndex + i] }
            day.slots = {
              ...day.slots,
              [slotType]: {
                id: meal.id,
                name: meal.name,
                emoji: meal.emoji,
                isLeftover: !isFirst,
                chainPosition: isFirst ? 'start' : isLast ? 'end' : 'middle',
                portionsRemaining: meal.portions - i,
              },
            }
            newDays[dayIndex + i] = day
          }
        } else {
          const day = { ...newDays[dayIndex] }
          day.slots = {
            ...day.slots,
            [slotType]: {
              id: meal.id,
              name: meal.name,
              emoji: meal.emoji,
              isLeftover: false,
            },
          }
          newDays[dayIndex] = day
        }

        return newDays
      })

      // API call
      try {
        const dayOfWeek = localDays?.[dayIndex]?.dayOfWeek ?? dayIndex
        await assignMeal(dayOfWeek, slotType, meal.id, createChain, chainDays)
      } catch (err) {
        console.error('Failed to assign meal:', err)
        // Refetch on error to restore correct state
        refetch()
      }
    },
    [assignMeal, localDays, refetch]
  )

  // Handle portion dialog confirm
  const handlePortionConfirm = ({ meal, dayIndex, slotType, createChain, chainDays }) => {
    handleAssignMeal(meal, dayIndex, slotType, createChain, chainDays)
  }

  // Remove meal from slot
  const handleMealRemove = useCallback(
    async (dayIndex, slot) => {
      const day = localDays?.[dayIndex]
      const slotData = day?.slots?.[slot]

      if (!slotData?.planMealId) {
        // If no planMealId, just clear locally (probably sample data)
        setLocalDays((prev) => {
          if (!prev) return prev
          const newDays = [...prev]
          const newDay = { ...newDays[dayIndex] }
          const newSlots = { ...newDay.slots }
          delete newSlots[slot]
          newDay.slots = newSlots
          newDays[dayIndex] = newDay
          return newDays
        })
        return
      }

      // Optimistic update
      setLocalDays((prev) => {
        if (!prev) return prev
        const newDays = [...prev]
        const newDay = { ...newDays[dayIndex] }
        const newSlots = { ...newDay.slots }
        delete newSlots[slot]
        newDay.slots = newSlots
        newDays[dayIndex] = newDay
        return newDays
      })

      try {
        await removeMeal(slotData.planMealId, false)
      } catch (err) {
        console.error('Failed to remove meal:', err)
        refetch()
      }
    },
    [localDays, removeMeal, refetch]
  )

  const handleMealClick = (meal) => {
    console.log('Meal clicked:', meal)
  }

  // Generate menu handler
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerateMenu = async () => {
    setIsGenerating(true)
    try {
      await plans.generatePlan({
        year,
        week,
        randomness: 0.3,
        save: true,
        force: true,  // Allow overwriting existing plans
      })
      // Refresh the board to show generated plan
      refetch()
    } catch (err) {
      console.error('Failed to generate menu:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  // Loading state
  if (loading && !localDays) {
    return <LoadingPage message="Étlap betöltése..." />
  }

  // Error state
  if (error && !localDays) {
    return (
      <ErrorPage
        title="Nem sikerült betölteni az étlapot"
        message={error}
        onRetry={refetch}
      />
    )
  }

  // Get pool data from API or use empty arrays
  const poolMeals = boardData?.pool?.flatMap((section) => section.meals) || []
  const seasonalMeals = boardData?.suggestions || []
  const recentMeals = boardData?.recentlyUsed || []

  const sidebar = (
    <Sidebar>
      <MealPool
        meals={poolMeals}
        seasonalMeals={seasonalMeals}
        recentMeals={recentMeals}
        onMealClick={handleMealClick}
      />
    </Sidebar>
  )

  const actions = (
    <>
      <div className="flex gap-3">
        <Button
          icon="✨"
          variant="primary"
          onClick={handleGenerateMenu}
          disabled={isGenerating}
        >
          {isGenerating ? 'Generálás...' : 'Menü elkészítése'}
        </Button>
        <Button icon="✓" variant="secondary">Ellenőrzés</Button>
      </div>
      <div className="flex gap-3">
        <Button icon="📄" variant="secondary">PDF</Button>
        <Button icon="🛒" variant="secondary">Bevásárlólista</Button>
      </div>
    </>
  )

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <BoardLayout
        year={year}
        week={week}
        startDate={boardData?.startDate ? formatDateRange(boardData.startDate, boardData.endDate).split('–')[0].trim() : ''}
        endDate={boardData?.startDate ? formatDateRange(boardData.startDate, boardData.endDate).split('–')[1]?.trim() || '' : ''}
        onPrev={handlePrev}
        onNext={handleNext}
        onToday={handleToday}
        sidebar={sidebar}
        actions={actions}
      >
        <WeekGrid
          days={localDays || []}
          year={year}
          week={week}
          onMealRemove={handleMealRemove}
        />
      </BoardLayout>

      {/* Drag Overlay */}
      <DragOverlay dropAnimation={null}>
        {activeMeal ? <DragOverlayContent meal={activeMeal} /> : null}
      </DragOverlay>

      {/* Portion Dialog */}
      <PortionDialog
        isOpen={portionDialog.isOpen}
        onClose={() => setPortionDialog({ isOpen: false, meal: null, dayIndex: null, slotType: null })}
        meal={portionDialog.meal}
        dayIndex={portionDialog.dayIndex}
        slotType={portionDialog.slotType}
        maxDays={7}
        onConfirm={handlePortionConfirm}
      />
    </DndContext>
  )
}

export default App
