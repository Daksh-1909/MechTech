import React, { forwardRef } from 'react'
import { cn } from '../../lib/utils'

export type GlassVariant = 'subtle' | 'standard' | 'floating' | 'modal'
export type GlassGlow = 'cyan' | 'indigo' | 'emerald' | 'amber' | 'rose' | 'none'

export interface GlassSurfaceProps extends React.HTMLAttributes<HTMLElement> {
  as?: React.ElementType
  variant?: GlassVariant
  interactive?: boolean
  border?: boolean
  glow?: GlassGlow
  children?: React.ReactNode
  className?: string
}

const variantClasses: Record<GlassVariant, string> = {
  subtle: 'glass-material-subtle',
  standard: 'glass-material-standard',
  floating: 'glass-material-floating',
  modal: 'glass-material-modal',
}

const glowClasses: Record<GlassGlow, string> = {
  cyan: 'glass-glow-cyan',
  indigo: 'glass-glow-indigo',
  emerald: 'glass-glow-emerald',
  amber: 'glass-glow-amber',
  rose: 'glass-glow-rose',
  none: '',
}

export const GlassSurface = forwardRef<HTMLElement, GlassSurfaceProps>(
  (
    {
      as: Component = 'div',
      variant = 'standard',
      interactive = false,
      border = true,
      glow = 'none',
      className,
      children,
      tabIndex,
      role,
      ...props
    },
    ref,
  ) => {
    // If interactive and no tabIndex is specified and element is not natively interactive, supply tabIndex={0}
    const isInteractiveTag = Component === 'button' || Component === 'a'
    const computedTabIndex = interactive && !isInteractiveTag && tabIndex === undefined ? 0 : tabIndex
    const computedRole = interactive && !isInteractiveTag && role === undefined ? 'button' : role

    return (
      <Component
        ref={ref}
        role={computedRole}
        tabIndex={computedTabIndex}
        className={cn(
          'glass-surface-base',
          variantClasses[variant],
          interactive && 'glass-surface-interactive',
          !border && 'border-transparent shadow-none',
          glowClasses[glow],
          className,
        )}
        {...props}
      >
        {children}
      </Component>
    )
  },
)

GlassSurface.displayName = 'GlassSurface'

export default GlassSurface
