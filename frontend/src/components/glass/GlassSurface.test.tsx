import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { GlassSurface } from './GlassSurface'

describe('GlassSurface Component', () => {
  it('renders children correctly with default standard variant', () => {
    render(<GlassSurface>Content inside glass</GlassSurface>)

    const element = screen.getByText('Content inside glass')
    expect(element).toBeInTheDocument()
    expect(element).toHaveClass('glass-surface-base')
    expect(element).toHaveClass('glass-material-standard')
  })

  it('renders all four variants correctly', () => {
    const { rerender } = render(<GlassSurface variant="subtle">Subtle</GlassSurface>)
    expect(screen.getByText('Subtle')).toHaveClass('glass-material-subtle')

    rerender(<GlassSurface variant="standard">Standard</GlassSurface>)
    expect(screen.getByText('Standard')).toHaveClass('glass-material-standard')

    rerender(<GlassSurface variant="floating">Floating</GlassSurface>)
    expect(screen.getByText('Floating')).toHaveClass('glass-material-floating')

    rerender(<GlassSurface variant="modal">Modal</GlassSurface>)
    expect(screen.getByText('Modal')).toHaveClass('glass-material-modal')
  })

  it('applies interactive class, role="button", and tabIndex={0} when interactive is true on a div', () => {
    render(<GlassSurface interactive>Clickable Glass</GlassSurface>)

    const element = screen.getByText('Clickable Glass')
    expect(element).toHaveClass('glass-surface-interactive')
    expect(element).toHaveAttribute('role', 'button')
    expect(element).toHaveAttribute('tabIndex', '0')
  })

  it('preserves native attributes on native interactive tags like button', () => {
    render(
      <GlassSurface as="button" interactive>
        Native Glass Button
      </GlassSurface>,
    )

    const button = screen.getByRole('button', { name: 'Native Glass Button' })
    expect(button.tagName.toLowerCase()).toBe('button')
    expect(button).toHaveClass('glass-surface-interactive')
    // Should not explicitly override tabIndex on native button
    expect(button).not.toHaveAttribute('tabIndex')
  })

  it('renders polymorphic elements with custom as prop', () => {
    render(<GlassSurface as="section">Section Glass</GlassSurface>)

    const element = screen.getByText('Section Glass')
    expect(element.tagName.toLowerCase()).toBe('section')
  })

  it('applies glow classes correctly', () => {
    const { rerender } = render(<GlassSurface glow="cyan">Cyan Glow</GlassSurface>)
    expect(screen.getByText('Cyan Glow')).toHaveClass('glass-glow-cyan')

    rerender(<GlassSurface glow="emerald">Emerald Glow</GlassSurface>)
    expect(screen.getByText('Emerald Glow')).toHaveClass('glass-glow-emerald')
  })

  it('supports custom className concatenation', () => {
    render(<GlassSurface className="custom-test-class p-8">Custom</GlassSurface>)

    const element = screen.getByText('Custom')
    expect(element).toHaveClass('custom-test-class')
    expect(element).toHaveClass('p-8')
    expect(element).toHaveClass('glass-surface-base')
  })
})
