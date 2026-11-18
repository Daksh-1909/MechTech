import React, { useRef } from 'react'
import { motion, useMotionValue, useSpring, useReducedMotion, type HTMLMotionProps } from 'framer-motion'

export interface MagneticControlProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  strength?: number
  className?: string
  disabled?: boolean
}

export const MagneticControl: React.FC<MagneticControlProps> = ({
  children,
  strength = 0.22,
  className = '',
  disabled = false,
  ...props
}) => {
  const ref = useRef<HTMLDivElement>(null)
  const reduceMotion = useReducedMotion()

  const x = useMotionValue(0)
  const y = useMotionValue(0)

  // Natural elastic spring response
  const springConfig = { damping: 22, stiffness: 260, mass: 0.6 }
  const springX = useSpring(x, springConfig)
  const springY = useSpring(y, springConfig)

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (disabled || reduceMotion || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const distanceX = (e.clientX - centerX) * strength
    const distanceY = (e.clientY - centerY) * strength
    x.set(distanceX)
    y.set(distanceY)
  }

  const handlePointerLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      style={reduceMotion || disabled ? undefined : { x: springX, y: springY }}
      className={`inline-block ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default MagneticControl
