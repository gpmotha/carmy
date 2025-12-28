// Export API endpoints
import { get } from './client'

const API_BASE = '/api'

// Export as JSON
export function exportJson(year, week) {
  return get(`/export/${year}/${week}/json`)
}

// Export as CSV (returns text)
export async function exportCsv(year, week) {
  const response = await fetch(`${API_BASE}/export/${year}/${week}/csv`)
  return response.text()
}

// Export as Markdown (returns text)
export async function exportMarkdown(year, week) {
  const response = await fetch(`${API_BASE}/export/${year}/${week}/markdown`)
  return response.text()
}

// Export as ICS calendar (returns text)
export async function exportIcs(year, week) {
  const response = await fetch(`${API_BASE}/export/${year}/${week}/ics`)
  return response.text()
}

// Export shopping list (returns text)
export async function exportShopping(year, week) {
  const response = await fetch(`${API_BASE}/export/${year}/${week}/shopping`)
  return response.text()
}

// Download helper - triggers browser download
export function downloadFile(content, filename, type = 'text/plain') {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
