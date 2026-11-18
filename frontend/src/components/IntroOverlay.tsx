import React, { useEffect, useState, useCallback } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'

const SESSION_KEY = 'mechtech-intro-seen'
const TITLE = 'MechTech.'
const SLOGAN = 'Industrial Intelligence & Predictive Diagnostics'

export const IntroOverlay: React.FC = () => {
  const reduceMotion = useReducedMotion()
  const [visible, setVisible] = useState(() => {
    try {
      return !sessionStorage.getItem(SESSION_KEY)
    } catch {
      return false
    }
  })

  const dismiss = useCallback(() => {
    setVisible(false)
    try {
      sessionStorage.setItem(SESSION_KEY, '1')
    } catch {
      // Storage access restricted
    }
  }, [])

  // Auto-dismiss after sequence completes (~1.85s)
  useEffect(() => {
    if (!visible) return

    const timer = window.setTimeout(
      () => {
        dismiss()
      },
      reduceMotion ? 350 : 1850,
    )

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        dismiss()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.clearTimeout(timer)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [visible, reduceMotion, dismiss])

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#171717] text-[#F5F5F2] select-none overflow-hidden"
          role="status"
          aria-label="MechTech introductory sequence"
          initial={{ opacity: 1 }}
          exit={{
            opacity: 0,
            transition: { duration: reduceMotion ? 0.15 : 0.45, ease: 'easeInOut' },
          }}
        >
          {/* Subtle Ambient Matte Backdrop Reflection */}
          <div
            className="absolute inset-0 pointer-events-none opacity-20"
            style={{
              backgroundImage:
                'radial-gradient(circle at 50% 50%, rgba(255, 90, 54, 0.12) 0%, transparent 65%)',
            }}
          />

          {/* Accessible Skip Button */}
          <button
            type="button"
            onClick={dismiss}
            className="absolute top-6 right-6 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/15 bg-white/5 font-mono text-[11px] text-white/60 hover:text-white hover:border-[#FF5A36] transition-colors"
          >
            <span>Skip</span>
            <kbd className="px-1 py-0.5 rounded bg-white/10 text-[9px] text-[#FF5A36]">ESC</kbd>
          </button>

          {/* Central Cinematic Lockup */}
          <motion.div
            className="relative z-10 w-[min(90vw,720px)] text-center px-4"
            initial={reduceMotion ? { opacity: 1 } : { scale: 1.02 }}
            animate={reduceMotion ? { opacity: 1 } : { scale: [1.02, 1, 0.98] }}
            transition={{ duration: 1.8, times: [0, 0.7, 1], ease: 'easeOut' }}
          >
            {/* Crossfade Typewriter Brand Title */}
            <div className="flex items-center justify-center">
              <h1 className="font-sans font-bold text-5xl sm:text-7xl md:text-8xl tracking-tighter text-[#F5F5F2] flex items-center">
                {TITLE.split('').map((char, i) => (
                  <motion.span
                    key={i}
                    initial={
                      reduceMotion
                        ? { opacity: 1 }
                        : { opacity: 0, filter: 'blur(8px)', y: 8 }
                    }
                    animate={
                      reduceMotion
                        ? { opacity: 1 }
                        : { opacity: 1, filter: 'blur(0px)', y: 0 }
                    }
                    transition={{
                      delay: reduceMotion ? 0 : 0.08 + i * 0.045,
                      duration: 0.35,
                      ease: 'easeOut',
                    }}
                    className={char === '.' ? 'text-[#FF5A36]' : ''}
                  >
                    {char}
                  </motion.span>
                ))}
              </h1>

              {/* Blinking Signal Orange Caret */}
              {!reduceMotion && (
                <motion.span
                  className="inline-block w-1 h-10 sm:h-14 md:h-16 ml-1.5 bg-[#FF5A36] rounded-full"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ duration: 0.8, repeat: 2, ease: 'easeInOut' }}
                />
              )}
            </div>

            {/* Slogan Crossfade Reveal */}
            <div className="mt-3 overflow-hidden">
              <motion.p
                initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 10, filter: 'blur(4px)' }}
                animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, filter: 'blur(0px)' }}
                transition={{
                  delay: reduceMotion ? 0 : 0.58,
                  duration: 0.6,
                  ease: 'easeOut',
                }}
                className="font-mono text-xs sm:text-sm tracking-[0.22em] uppercase text-[#F5F5F2]/75"
              >
                {SLOGAN}
              </motion.p>
            </div>

            {/* Thin Signal Orange Rule Draw */}
            <motion.div
              className="mt-6 mx-auto h-[2px] w-full max-w-md bg-[#FF5A36] origin-left rounded-full shadow-[0_0_12px_rgba(255,90,54,0.4)]"
              initial={reduceMotion ? { scaleX: 1 } : { scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{
                delay: reduceMotion ? 0 : 0.72,
                duration: reduceMotion ? 0.1 : 0.55,
                ease: [0.16, 1, 0.3, 1],
              }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default IntroOverlay
