import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '../../lib/utils'

interface FloatingPathsProps {
  position: number
  pathColor?: string
  accentColor?: string
}

function FloatingPaths({
  position,
  pathColor = 'currentColor',
  accentColor = '#FF5A36',
}: FloatingPathsProps) {
  const reduceMotion = useReducedMotion()

  const paths = Array.from({ length: 36 }, (_, i) => {
    const isAccent = i % 7 === 0 // 10% signal orange accent distribution
    return {
      id: i,
      d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${380 - i * 5 * position} -${
        189 + i * 6
      } -${312 - i * 5 * position} ${216 - i * 6} ${152 - i * 5 * position} ${
        343 - i * 6
      }C${616 - i * 5 * position} ${470 - i * 6} ${684 - i * 5 * position} ${
        875 - i * 6
      } ${684 - i * 5 * position} ${875 - i * 6}`,
      width: 0.5 + i * 0.03,
      stroke: isAccent ? accentColor : pathColor,
      strokeOpacity: isAccent ? 0.35 : 0.08 + (i / 36) * 0.18,
      duration: 20 + (i % 8) * 2.5,
    }
  })

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none" aria-hidden="true">
      <svg
        className="w-full h-full"
        viewBox="0 0 696 316"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
      >
        <title>Background Paths</title>
        {paths.map((path) => (
          <motion.path
            key={path.id}
            d={path.d}
            stroke={path.stroke}
            strokeWidth={path.width}
            strokeOpacity={path.strokeOpacity}
            initial={reduceMotion ? { pathLength: 1, opacity: path.strokeOpacity } : { pathLength: 0.3, opacity: 0.4 }}
            animate={
              reduceMotion
                ? undefined
                : {
                    pathLength: 1,
                    opacity: [0.2, path.strokeOpacity, 0.2],
                    pathOffset: [0, 1, 0],
                  }
            }
            transition={
              reduceMotion
                ? undefined
                : {
                    duration: path.duration,
                    repeat: Number.POSITIVE_INFINITY,
                    ease: 'linear',
                  }
            }
          />
        ))}
      </svg>
    </div>
  )
}

export interface BackgroundPathsProps {
  title?: string
  subtitle?: string
  className?: string
  pathColor?: string
  accentColor?: string
  opacity?: number
  children?: React.ReactNode
}

export function BackgroundPaths({
  title,
  subtitle,
  className = '',
  pathColor = 'currentColor',
  accentColor = '#FF5A36',
  opacity = 0.85,
  children,
}: BackgroundPathsProps) {
  const words = title ? title.split(' ') : []

  return (
    <div
      className={cn(
        'relative w-full flex items-center justify-center overflow-hidden bg-canvas transition-colors duration-300',
        className,
      )}
    >
      <div className="absolute inset-0 pointer-events-none" style={{ opacity }}>
        <FloatingPaths position={1} pathColor={pathColor} accentColor={accentColor} />
        <FloatingPaths position={-1} pathColor={pathColor} accentColor={accentColor} />
      </div>

      {children ? (
        <div className="relative z-10 w-full">{children}</div>
      ) : title ? (
        <div className="relative z-10 container mx-auto px-4 md:px-6 text-center py-20">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
            className="max-w-4xl mx-auto"
          >
            <h1 className="text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-primary">
              {words.map((word, wordIndex) => (
                <span key={wordIndex} className="inline-block mr-3 last:mr-0">
                  {word.split('').map((letter, letterIndex) => (
                    <motion.span
                      key={`${wordIndex}-${letterIndex}`}
                      initial={{ y: 30, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      transition={{
                        delay: wordIndex * 0.08 + letterIndex * 0.025,
                        type: 'spring',
                        stiffness: 180,
                        damping: 24,
                      }}
                      className="inline-block"
                    >
                      {letter}
                    </motion.span>
                  ))}
                </span>
              ))}
            </h1>
            {subtitle && (
              <p className="mt-4 font-mono text-xs sm:text-sm uppercase tracking-[0.2em] text-secondary">
                {subtitle}
              </p>
            )}
          </motion.div>
        </div>
      ) : null}
    </div>
  )
}

export default BackgroundPaths
