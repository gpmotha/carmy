// Board/Planning API endpoints
import { get, post, put, del } from './client'

// Get week board data (includes pool, suggestions, recent meals)
export function getWeekBoard(year, week) {
  return get(`/board/week/${year}/${week}`)
}

// Get current week board
export function getCurrentWeekBoard() {
  return get('/board/current')
}

// Get month board data
export function getMonthBoard(year, month) {
  return get(`/board/month/${year}/${month}`)
}

// Get current month board
export function getCurrentMonthBoard() {
  return get('/board/month/current')
}

// Assign meal to slot
export function assignMealToSlot(data) {
  return post('/board/slot', data)
}

// Update slot
export function updateSlot(planMealId, updates) {
  return put(`/board/slot/${planMealId}`, updates)
}

// Remove meal from slot
export function removeSlot(planMealId, breakChain = false) {
  return del(`/board/slot/${planMealId}`, { break_chain: breakChain })
}

// Extend leftover chain
export function extendChain(chainId, days = 1) {
  return post(`/board/chain/${chainId}/extend`, null, { days })
}

// Shrink leftover chain
export function shrinkChain(chainId) {
  return post(`/board/chain/${chainId}/shrink`)
}

// Delete entire chain
export function deleteChain(chainId) {
  return del(`/board/chain/${chainId}`)
}
