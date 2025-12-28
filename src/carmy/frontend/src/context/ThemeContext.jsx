import { createContext, useContext, useState, useEffect } from 'react'
import { themes, defaultTheme } from '../config/themes'

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
  const [themeName, setThemeName] = useState(() => {
    // Load from localStorage or use default
    const saved = localStorage.getItem('carmy-theme')
    return saved && themes[saved] ? saved : defaultTheme
  })

  const theme = themes[themeName]

  // Save to localStorage when theme changes
  useEffect(() => {
    localStorage.setItem('carmy-theme', themeName)
  }, [themeName])

  const setTheme = (name) => {
    if (themes[name]) {
      setThemeName(name)
    }
  }

  const toggleTheme = () => {
    setThemeName(current => current === 'provance' ? 'bear' : 'provance')
  }

  return (
    <ThemeContext.Provider value={{ theme, themeName, setTheme, toggleTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export default ThemeContext
