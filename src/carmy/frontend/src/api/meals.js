// Meals API endpoints
import { get, post, put, del } from './client'

// List meals with optional filters
export function getMeals(filters = {}) {
  return get('/meals', filters)
}

// Get single meal by ID
export function getMeal(id) {
  return get(`/meals/${id}`)
}

// Create new meal
export function createMeal(data) {
  return post('/meals', data)
}

// Update meal
export function updateMeal(id, data) {
  return put(`/meals/${id}`, data)
}

// Delete meal
export function deleteMeal(id) {
  return del(`/meals/${id}`)
}

// Get meal types
export function getMealTypes() {
  return get('/meals/types')
}

// Get cuisines
export function getCuisines() {
  return get('/meals/cuisines')
}

// Search meals (for pool sidebar)
export function searchMeals(query) {
  return get('/board/search', { q: query })
}
