import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Activity, ArrowRight, Gauge, Layers, Moon, Sun, Laptop, Waves, Play, Sparkles } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import { BackgroundPaths } from '../components/ui/BackgroundPaths'
import { MagneticControl } from '../components/glass/MagneticControl'

const spring = { type: 'spring' as const, stiffness: 400, damping: 30, mass: 0.6 }

export default function DesignPlaygroundPage() {
  const { theme, resolvedTheme, setTheme } = useTheme()
  const [activeTab, setActiveTab] = useState('Materials')
  const [showTypewriterDemo, setShowTypewriterDemo] = useState(false)
  const reduceMotion = useReducedMotion()

  const tabs = ['Materials', 'Motion', 'UI Hub Lines', 'Telemetry']

  const triggerTypewriterDemo = () => {
    setShowTypewriterDemo(false)
    setTimeout(() => setShowTypewriterDemo(true), 50)
  }

  return (
    <main className="playground relative mx-auto min-h-screen max-w-6xl space-y-12 px-5 py-10 sm:px-8">
      {/* Header Bar */}
      <header className="flex flex-wrap items-end justify-between gap-6 border-b border-border pb-8">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-mono text-[11px] font-semibold text-accent uppercase tracking-wider">
              <Sparkles className="size-3" />
              Visual Identity & Liquid Motion Upgrade
            </span>
          </div>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-primary sm:text-5xl">
            Matte Monochrome + Signal Orange
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-secondary">
            Strict 3-colour palette (70% Matte White, 25% Matte Black, 5% Signal Orange) paired with
            elastic liquid glass interactions and typography powered by Geist Sans and Geist Mono.
          </p>
        </div>

        {/* Theme Switcher with Elastic Active Pill */}
        <div className="glass-material-floating flex rounded-xl border border-border p-1.5" role="group" aria-label="Color theme">
          {([
            { id: 'light', Icon: Sun, label: 'Light' },
            { id: 'dark', Icon: Moon, label: 'Dark' },
            { id: 'system', Icon: Laptop, label: 'System' },
          ] as const).map(({ id, Icon, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTheme(id)}
              aria-pressed={theme === id}
              className="relative flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-medium capitalize text-secondary transition-colors hover:text-primary focus-visible:outline-accent"
            >
              {theme === id && (
                <motion.span
                  layoutId="theme-switch-indicator"
                  className="absolute inset-0 rounded-lg bg-accent/15 border border-accent/30 shadow-sm"
                  transition={reduceMotion ? { duration: 0 } : spring}
                />
              )}
              <Icon className="relative z-10 size-3.5" />
              <span className="relative z-10">{label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Section 1: Color System & Ratio Breakdown */}
      <section className="grid gap-6 lg:grid-cols-[1.3fr_.7fr]">
        <div className="playground-stage relative overflow-hidden rounded-2xl border border-border p-6 sm:p-8">
          <div className="flex items-center justify-between border-b border-border/80 pb-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
                70 / 25 / 5 Architecture · Active Mode: {resolvedTheme}
              </p>
              <h2 className="mt-1 text-lg font-semibold text-primary">Core Brand Ratio</h2>
            </div>
            <span className="font-mono text-xs font-bold text-accent">ZERO EXTRA COLORS</span>
          </div>

          {/* Visual Palette Bars */}
          <div className="mt-6 space-y-4">
            <div className="h-6 w-full overflow-hidden rounded-xl border border-border flex">
              <div className="bg-[#F5F5F2] text-[#171717] font-mono text-[10px] flex items-center justify-center font-bold" style={{ width: '70%' }}>
                70% Matte White
              </div>
              <div className="bg-[#171717] text-[#F5F5F2] font-mono text-[10px] flex items-center justify-center font-bold" style={{ width: '25%' }}>
                25% Black
              </div>
              <div className="bg-[#FF5A36] text-[#171717] font-mono text-[10px] flex items-center justify-center font-bold" style={{ width: '5%' }}>
                5%
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3.5 rounded-xl border border-border bg-surface">
                <span className="text-[10px] font-mono uppercase text-muted block">Primary (70%)</span>
                <span className="text-sm font-bold text-primary block mt-1">Matte White</span>
                <code className="text-xs font-mono text-secondary">#F5F5F2</code>
              </div>
              <div className="p-3.5 rounded-xl border border-border bg-surface">
                <span className="text-[10px] font-mono uppercase text-muted block">Secondary (25%)</span>
                <span className="text-sm font-bold text-primary block mt-1">Matte Black</span>
                <code className="text-xs font-mono text-secondary">#171717</code>
              </div>
              <div className="p-3.5 rounded-xl border border-border bg-surface">
                <span className="text-[10px] font-mono uppercase text-muted block">Signal Accent (5%)</span>
                <span className="text-sm font-bold text-accent block mt-1">Signal Orange</span>
                <code className="text-xs font-mono text-accent">#FF5A36</code>
              </div>
            </div>
          </div>
        </div>

        {/* Cinematic Intro Demo Trigger */}
        <aside className="glass-material-standard rounded-2xl border border-border p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-accent">
              <Play className="size-4" />
              <h2 className="text-sm font-semibold text-primary">Crossfade Typewriter</h2>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-secondary">
              Experience the cinematic letter-by-letter crossfade opening sequence with blinking signal orange caret and rule draw.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-border">
            <MagneticControl>
              <button
                type="button"
                onClick={triggerTypewriterDemo}
                className="glass-btn glass-btn-primary w-full justify-center text-xs font-semibold"
              >
                <Play className="size-3.5" />
                <span>Simulate Opening Sequence</span>
              </button>
            </MagneticControl>
          </div>
        </aside>
      </section>

      {/* Typewriter Inline Interactive Sandbox */}
      {showTypewriterDemo && (
        <section className="relative overflow-hidden rounded-2xl border border-border bg-[#171717] p-8 text-center text-[#F5F5F2]">
          <p className="font-mono text-[10px] uppercase tracking-widest text-[#F5F5F2]/50 mb-4">
            Live Crossfade Typewriter Simulation
          </p>
          <div className="flex items-center justify-center">
            <h3 className="font-sans font-bold text-4xl sm:text-6xl tracking-tighter">
              {'MechTech.'.split('').map((char, i) => (
                <motion.span
                  key={i}
                  initial={{ opacity: 0, filter: 'blur(8px)', y: 6 }}
                  animate={{ opacity: 1, filter: 'blur(0px)', y: 0 }}
                  transition={{ delay: 0.05 + i * 0.05, duration: 0.35 }}
                  className={char === '.' ? 'text-[#FF5A36]' : ''}
                >
                  {char}
                </motion.span>
              ))}
            </h3>
            <motion.span
              className="inline-block w-1 h-9 sm:h-12 ml-1.5 bg-[#FF5A36] rounded-full"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.8, repeat: 3 }}
            />
          </div>
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.65, duration: 0.5 }}
            className="mt-3 font-mono text-xs uppercase tracking-[0.2em] text-[#F5F5F2]/70"
          >
            Industrial Intelligence & Predictive Diagnostics
          </motion.p>
          <motion.div
            className="mt-5 mx-auto h-[2px] w-48 bg-[#FF5A36] origin-left rounded-full"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.75, duration: 0.5 }}
          />
        </section>
      )}

      {/* Section 2: Shared layoutId Elastic Tabs & Magnetic Hover */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
              Liquid Elasticity Motion / Reduced Motion: {reduceMotion ? 'Enabled' : 'Disabled'}
            </p>
            <h2 className="mt-1 text-2xl font-bold text-primary">Interactive Motion Primitives</h2>
          </div>

          {/* Segmented Elastic Tabs */}
          <div className="glass-material-subtle relative inline-flex rounded-xl border border-border p-1" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab}
                role="tab"
                aria-selected={activeTab === tab}
                onClick={() => setActiveTab(tab)}
                className="relative rounded-lg px-4 py-2 text-xs font-medium text-secondary transition-colors hover:text-primary focus-visible:outline-accent"
              >
                {activeTab === tab && (
                  <motion.span
                    layoutId="playground-feature-tab"
                    className="absolute inset-0 rounded-lg border border-accent/40 bg-accent/15 shadow-sm"
                    transition={reduceMotion ? { duration: 0 } : spring}
                  />
                )}
                <span className="relative z-10">{tab}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content Display */}
        <div className="glass-panel min-h-64 rounded-2xl border border-border p-6 sm:p-8">
          {activeTab === 'Materials' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <span className="flex size-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
                  <Layers className="size-5" />
                </span>
                <div>
                  <h3 className="text-base font-semibold text-primary">Matte Liquid Glass Hierarchy</h3>
                  <p className="text-xs text-secondary">
                    Calibrated backdrop diffusion with restrained specular highlights and zero colorful gloss.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { name: 'Subtle', blur: '8px', cls: 'glass-material-subtle', desc: 'Tab rails and embedded cards' },
                  { name: 'Standard', blur: '16px', cls: 'glass-material-standard', desc: 'Main telemetry and data panels' },
                  { name: 'Floating', blur: '22px', cls: 'glass-material-floating', desc: 'Floating toolbars and popovers' },
                  { name: 'Modal', blur: '28px', cls: 'glass-material-modal', desc: 'Modals and emergency alerts' },
                ].map((item) => (
                  <div key={item.name} className={`${item.cls} p-5 rounded-xl border border-border`}>
                    <span className="font-mono text-[10px] text-accent uppercase font-bold">{item.name}</span>
                    <p className="mt-2 text-sm font-semibold text-primary">{item.blur} Diffusion</p>
                    <p className="mt-1 text-xs text-muted leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'Motion' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <span className="flex size-10 items-center justify-center rounded-xl bg-accent/10 text-accent">
                  <Waves className="size-5" />
                </span>
                <div>
                  <h3 className="text-base font-semibold text-primary">Magnetic Pointer Attraction</h3>
                  <p className="text-xs text-secondary">
                    Gentle cursor-following magnetic pull with spring-loaded snap-back physics.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4 pt-4">
                <MagneticControl strength={0.3}>
                  <button type="button" className="glass-btn glass-btn-primary px-6 py-3 text-xs font-semibold">
                    <span>Magnetic Button (Strength 0.3)</span>
                    <ArrowRight className="size-3.5" />
                  </button>
                </MagneticControl>

                <MagneticControl strength={0.15}>
                  <button type="button" className="glass-btn px-6 py-3 text-xs font-semibold">
                    <span>Soft Magnetic Action (Strength 0.15)</span>
                  </button>
                </MagneticControl>
              </div>
            </div>
          )}

          {activeTab === 'UI Hub Lines' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-semibold text-primary">UI Hub Floating Paths Background</h3>
                <p className="text-xs text-secondary">
                  Cubic bezier animated vector paths rendered in SVG with 60:30:10 palette adaptation.
                </p>
              </div>

              <div className="relative h-64 w-full overflow-hidden rounded-xl border border-border bg-surface">
                <BackgroundPaths pathColor="currentColor" accentColor="#FF5A36" opacity={0.8} />
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4 pointer-events-none">
                  <h4 className="text-2xl font-bold tracking-tight text-primary">Floating Vectors</h4>
                  <p className="font-mono text-xs text-accent mt-1 uppercase tracking-widest">
                    Continuous Mathematical Curves
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'Telemetry' && (
            <div className="grid gap-4 sm:grid-cols-2">
              <article className="glass-panel p-5 rounded-xl border border-border">
                <div className="flex justify-between">
                  <span className="font-mono text-[10px] text-muted">INDUCTION MOTOR / A-102</span>
                  <Activity className="size-4 text-accent" />
                </div>
                <p className="mt-5 font-mono text-4xl tabular-nums text-primary font-bold">
                  1,482<span className="ml-2 text-sm text-secondary font-normal">rpm</span>
                </p>
                <p className="mt-1 text-xs text-muted">Shaft rotation · nominal operating zone</p>
                <div className="mt-5 flex h-10 items-end gap-1" aria-label="Sample telemetry">
                  <span className="telemetry-bar h-4" />
                  <span className="telemetry-bar h-7" />
                  <span className="telemetry-bar h-5" />
                  <span className="telemetry-bar h-9" />
                  <span className="telemetry-bar h-6" />
                  <span className="telemetry-bar h-10" />
                  <span className="telemetry-bar h-8" />
                </div>
              </article>

              <article className="glass-panel flex flex-col justify-between p-5 rounded-xl border border-border">
                <div className="flex justify-between">
                  <span className="font-mono text-[10px] text-muted">BEARING VIBRATION</span>
                  <Gauge className="size-4 text-secondary" />
                </div>
                <div>
                  <p className="mt-4 text-2xl font-bold text-primary font-mono tabular-nums">1.84 mm/s</p>
                  <p className="mt-1 text-xs text-muted">ISO 10816 Class A / Healthy Vibration Baseline</p>
                </div>
                <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-raised">
                  <div className="h-full w-[65%] rounded-full bg-accent" />
                </div>
              </article>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}
