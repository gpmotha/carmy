// Plans API endpoints
import { get, post } from './client'

// List plans
export function getPlans(filters = {}) {
  return get('/plans', filters)
}

// Get current week plan
export function getCurrentPlan() {
  return get('/plans/current')
}

// Get specific plan
export function getPlan(year, week) {
  return get(`/plans/${year}/${week}`)
}

// Validate plan
export function validatePlan(year, week) {
  return get(`/plans/${year}/${week}/validate`)
}

// Generate plan (uses query params, not body)
export function generatePlan(options = {}) {
  const { week, year, randomness = 0.3, save = false, force = false } = options
  const params = new URLSearchParams()
  if (week !== undefined) params.append('week', week)
  if (year !== undefined) params.append('year', year)
  params.append('randomness', randomness)
  params.append('save', save)
  params.append('force', force)
  const query = params.toString()
  return post(`/plans/generate?${query}`, null)
}
