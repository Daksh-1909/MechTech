import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ThemeProvider } from './ThemeProvider'
import { useTheme } from '../hooks/useTheme'

const TestConsumer: React.FC = () => {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-val">{theme}</span>
      <span data-testid="resolved-theme-val">{resolvedTheme}</span>
      <button onClick={() => setTheme('light')}>Set Light</button>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
      <button onClick={() => setTheme('system')}>Set System</button>
      <button onClick={toggleTheme}>Toggle Theme</button>
    </div>
  )
}

describe('ThemeProvider & useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.className = ''
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('provides default theme and resolves correctly', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <TestConsumer />
      </ThemeProvider>,
    )

    expect(screen.getByTestId('theme-val').textContent).toBe('light')
    expect(screen.getByTestId('resolved-theme-val').textContent).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(document.documentElement.classList.contains('light')).toBe(true)
  })

  it('persists theme change to localStorage and updates DOM classes', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <TestConsumer />
      </ThemeProvider>,
    )

    fireEvent.click(screen.getByText('Set Dark'))

    expect(screen.getByTestId('theme-val').textContent).toBe('dark')
    expect(screen.getByTestId('resolved-theme-val').textContent).toBe('dark')
    expect(localStorage.getItem('mechtech-theme')).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggles between light and dark themes', () => {
    render(
      <ThemeProvider defaultTheme="light">
        <TestConsumer />
      </ThemeProvider>,
    )

    fireEvent.click(screen.getByText('Toggle Theme'))
    expect(screen.getByTestId('theme-val').textContent).toBe('dark')

    fireEvent.click(screen.getByText('Toggle Theme'))
    expect(screen.getByTestId('theme-val').textContent).toBe('light')
  })

  it('restores theme from localStorage on initial render', () => {
    localStorage.setItem('mechtech-theme', 'dark')

    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    )

    expect(screen.getByTestId('theme-val').textContent).toBe('dark')
    expect(screen.getByTestId('resolved-theme-val').textContent).toBe('dark')
  })

  it('handles system preference detection', () => {
    // Mock system preference as dark
    vi.spyOn(window, 'matchMedia').mockImplementation((query: string) => ({
      matches: query.includes('prefers-color-scheme: dark'),
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }))

    render(
      <ThemeProvider defaultTheme="system">
        <TestConsumer />
      </ThemeProvider>,
    )

    expect(screen.getByTestId('theme-val').textContent).toBe('system')
    expect(screen.getByTestId('resolved-theme-val').textContent).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })
})
