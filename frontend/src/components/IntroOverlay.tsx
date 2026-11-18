import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'

const SESSION_KEY = 'mechtech-intro-seen'

export function IntroOverlay() {
  const reduceMotion = useReducedMotion()
  const [visible, setVisible] = useState(() => {
    try { return !sessionStorage.getItem(SESSION_KEY) } catch { return false }
  })

  useEffect(() => {
    if (!visible) return
    const finish = window.setTimeout(() => {
      setVisible(false)
      try { sessionStorage.setItem(SESSION_KEY, '1') } catch { /* Storage may be disabled. */ }
    }, reduceMotion ? 450 : 1750)
    return () => window.clearTimeout(finish)
  }, [visible, reduceMotion])

  const skip = () => {
    setVisible(false)
    try { sessionStorage.setItem(SESSION_KEY, '1') } catch { /* Storage may be disabled. */ }
  }

  return (
    <AnimatePresence>
      {visible && <motion.div className="intro-overlay" role="status" aria-label="MechTech" initial={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: reduceMotion ? 0.12 : 0.55, ease: 'easeInOut' } }}>
        <button type="button" className="intro-skip" onClick={skip}>Skip intro <span aria-hidden="true">↗</span></button>
        <div className="intro-lockup">
          <motion.h1 initial={{ opacity: 0, filter: 'blur(14px)', scale: 1.04 }} animate={{ opacity: 1, filter: 'blur(0px)', scale: [1.04, 1, 0.97] }} transition={{ duration: reduceMotion ? 0.12 : 1.05, times: [0, 0.7, 1], ease: 'easeOut' }}>MechTech.</motion.h1>
          <motion.span className="intro-rule" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: reduceMotion ? 0 : 0.72, duration: reduceMotion ? 0.12 : 0.5, ease: 'easeOut' }} />
        </div>
      </motion.div>}
    </AnimatePresence>
  )
}
