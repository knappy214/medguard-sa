import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // State
  const currentTheme = ref<'light' | 'dark'>('light')
  const isInitialized = ref(false)

  // Actions
  const setTheme = (theme: 'light' | 'dark') => {
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('medguard-theme', theme)
  }

  const toggleTheme = () => {
    const newTheme = currentTheme.value === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }

  const initializeTheme = () => {
    if (isInitialized.value) return

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('medguard-theme') as 'light' | 'dark' | null
    
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      setTheme(savedTheme)
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setTheme(prefersDark ? 'dark' : 'light')
    }

    isInitialized.value = true
  }

  const resetToSystemPreference = () => {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setTheme(prefersDark ? 'dark' : 'light')
    localStorage.removeItem('medguard-theme')
  }

  // Watch for system theme changes
  if (typeof window !== 'undefined') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    mediaQuery.addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem('medguard-theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    })
  }

  return {
    // State
    currentTheme,
    isInitialized,
    
    // Actions
    setTheme,
    toggleTheme,
    initializeTheme,
    resetToSystemPreference
  }
}) 