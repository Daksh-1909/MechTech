import React, { useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '../../lib/utils'

export interface BackgroundPathsProps {
  title?: string
  subtitle?: string
  className?: string
  pathColor?: string
  accentColor?: string
  opacity?: number
  children?: React.ReactNode
}

interface PathDef {
  id: string
  d: string
  width: number
  stroke: string
  strokeOpacity: number
  duration: number
  delay: number
}

function generatePaths(position: number, pathColor: string, accentColor: string): PathDef[] {
  // 20 calibrated paths per side (40 total) for optimal density and 60fps GPU performance
  return Array.from({ length: 20 }, (_, i) => {
    const isAccent = i % 5 === 0 // 10% Signal Orange accent distribution
    return {
      id: `${position}-${i}`,
      d: `M-${380 - i * 9 * position} -${189 + i * 10}C-${380 - i * 9 * position} -${
        189 + i * 10
      } -${312 - i * 9 * position} ${216 - i * 10} ${152 - i * 9 * position} ${
        343 - i * 10
      }C${616 - i * 9 * position} ${470 - i * 10} ${684 - i * 9 * position} ${
        875 - i * 10
      } ${684 - i * 9 * position} ${875 - i * 10}`,
      width: isAccent ? 1.6 : 0.85 + (i / 20) * 0.75,
      stroke: isAccent ? accentColor : pathColor,
      strokeOpacity: isAccent ? 0.85 : 0.18 + (i / 20) * 0.32,
      duration: 18 + (i % 5) * 3.5,
      delay: -(i * 1.8),
    }
  })
}

export const BackgroundPaths: React.FC<BackgroundPathsProps> = ({
  title,
  subtitle,
  className = '',
  pathColor = '#171717',
  accentColor = '#FF5A36',
  opacity = 1,
  children,
}) => {
  const reduceMotion = useReducedMotion()

  const pathsGroup1 = useMemo(
    () => generatePaths(1, pathColor, accentColor),
    [pathColor, accentColor],
  )
  const pathsGroup2 = useMemo(
    () => generatePaths(-1, pathColor, accentColor),
    [pathColor, accentColor],
  )

  const words = title ? title.split(' ') : []

  return (
    <div
      className={cn(
        'relative min-h-[350px] h-full w-full flex items-center justify-center overflow-hidden transition-colors duration-300',
        className,
      )}
      style={{
        contain: 'strict',
        transform: 'translateZ(0)',
        backfaceVisibility: 'hidden',
      }}
    >
      {/* Single Unified High-Performance Hardware-Accelerated SVG Layer */}
      <div className="absolute inset-0 pointer-events-none select-none" style={{ opacity }}>
        <svg
          className="w-full h-full"
          viewBox="0 0 696 316"
          fill="none"
          preserveAspectRatio="xMidYMid slice"
          shapeRendering="geometricPrecision"
        >
          <title>UI Hub Floating Background Paths</title>

          {/* Group 1: Flowing forward with GPU float */}
          <g className={reduceMotion ? undefined : 'ui-hub-group-1'}>
            {pathsGroup1.map((p) => (
              <path
                key={p.id}
                d={p.d}
                stroke={p.stroke}
                strokeWidth={p.width}
                strokeOpacity={p.strokeOpacity}
                strokeLinecap="round"
                className={reduceMotion ? undefined : 'ui-hub-path-flow'}
                style={
                  reduceMotion
                    ? undefined
                    : {
                        animationDuration: `${p.duration}s`,
                        animationDelay: `${p.delay}s`,
                      }
                }
              />
            ))}
          </g>

          {/* Group 2: Flowing in counter-harmony with GPU float */}
          <g className={reduceMotion ? undefined : 'ui-hub-group-2'}>
            {pathsGroup2.map((p) => (
              <path
                key={p.id}
                d={p.d}
                stroke={p.stroke}
                strokeWidth={p.width}
                strokeOpacity={p.strokeOpacity}
                strokeLinecap="round"
                className={reduceMotion ? undefined : 'ui-hub-path-flow'}
                style={
                  reduceMotion
                    ? undefined
                    : {
                        animationDuration: `${p.duration}s`,
                        animationDelay: `${p.delay}s`,
                      }
                }
              />
            ))}
          </g>
        </svg>
      </div>

      {children ? (
        <div className="relative z-10 w-full h-full">{children}</div>
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
