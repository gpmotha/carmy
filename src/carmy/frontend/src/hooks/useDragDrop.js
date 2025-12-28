import { useState, useCallback } from 'react'

/**
 * Custom hook for managing drag and drop state
 */
export function useDragDrop({ onDrop }) {
  const [activeId, setActiveId] = useState(null)
  const [activeMeal, setActiveMeal] = useState(null)
  const [overSlot, setOverSlot] = useState(null)

  const handleDragStart = useCallback((event) => {
    const { active } = event
    setActiveId(active.id)
    setActiveMeal(active.data.current?.meal || null)
  }, [])

  const handleDragOver = useCallback((event) => {
    const { over } = event
    if (over) {
      setOverSlot(over.id)
    } else {
      setOverSlot(null)
    }
  }, [])

  const handleDragEnd = useCallback((event) => {
    const { active, over } = event

    if (over && active.data.current?.meal) {
      const meal = active.data.current.meal
      const [dayIndex, slotType] = over.id.split('-')

      onDrop?.({
        meal,
        dayIndex: parseInt(dayIndex),
        slotType,
      })
    }

    setActiveId(null)
    setActiveMeal(null)
    setOverSlot(null)
  }, [onDrop])

  const handleDragCancel = useCallback(() => {
    setActiveId(null)
    setActiveMeal(null)
    setOverSlot(null)
  }, [])

  return {
    activeId,
    activeMeal,
    overSlot,
    handleDragStart,
    handleDragOver,
    handleDragEnd,
    handleDragCancel,
  }
}

export default useDragDrop
