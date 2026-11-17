import React, { useState } from 'react'
import { useTheme } from '../hooks/useTheme'
import GlassSurface, { type GlassVariant, type GlassGlow } from '../components/glass/GlassSurface'
import {
  Sun,
  Moon,
  Laptop,
  Layers,
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  ShieldCheck,
  Eye,
  Activity,
  ArrowRight,
  RefreshCw,
} from 'lucide-react'

export const DesignPlaygroundPage: React.FC = () => {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme()
  const [selectedVariant, setSelectedVariant] = useState<GlassVariant>('standard')
  const [selectedGlow, setSelectedGlow] = useState<GlassGlow>('cyan')
  const [interactiveCounter, setInteractiveCounter] = useState(0)
  const [sliderVal, setSliderVal] = useState(65)
  const [inputVal, setInputVal] = useState('Industrial Motor Core A-102')

  const variants: { key: GlassVariant; title: string; blur: string; desc: string }[] = [
    {
      key: 'subtle',
      title: 'Subtle Glass',
      blur: '~8px Blur (140% Saturation)',
      desc: 'Ideal for embedded cards, secondary panels, tab rails, and low-contrast backdrops.',
    },
    {
      key: 'standard',
      title: 'Standard Glass',
      blur: '~16px Blur (180% Saturation)',
      desc: 'Core interface workhorse: telemetry panels, data cards, navigational bars, and toolbars.',
    },
    {
      key: 'floating',
      title: 'Floating Glass',
      blur: '~24px Blur (200% Saturation)',
      desc: 'Elevated elements: dropdown popovers, floating action bars, tooltips, and header navigation.',
    },
    {
      key: 'modal',
      title: 'Modal Glass',
      blur: '~28px Blur (210% Saturation)',
      desc: 'Maximum depth & isolation: modal dialogs, critical alert overlays, and prominent drawers.',
    },
  ]

  const glows: { key: GlassGlow; label: string; color: string }[] = [
    { key: 'none', label: 'None', color: 'bg-slate-500' },
    { key: 'cyan', label: 'Cyan Core', color: 'bg-cyan-400' },
    { key: 'indigo', label: 'Indigo Flux', color: 'bg-indigo-400' },
    { key: 'emerald', label: 'Emerald OK', color: 'bg-emerald-400' },
    { key: 'amber', label: 'Amber Warn', color: 'bg-amber-400' },
    { key: 'rose', label: 'Rose Critical', color: 'bg-rose-400' },
  ]

  return (
    <div className="relative min-h-screen bg-canvas text-primary transition-colors duration-300">
      {/* Dynamic Ambient Background Gradients to stress-test translucent liquid glass blur */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden opacity-40 dark:opacity-25" aria-hidden="true">
        <div className="absolute -top-40 -left-40 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-blue-500/30 to-cyan-400/20 blur-3xl" />
        <div className="absolute top-1/3 -right-40 h-[700px] w-[700px] rounded-full bg-gradient-to-bl from-indigo-500/25 to-purple-500/20 blur-3xl" />
        <div className="absolute -bottom-40 left-1/4 h-[650px] w-[650px] rounded-full bg-gradient-to-tr from-cyan-500/20 to-teal-400/25 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-12">
        {/* Header Bar */}
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-mono text-xs font-semibold text-accent">
                <Sparkles className="h-3.5 w-3.5" />
                Phase 1 Design Foundation
              </span>
              <span className="font-mono text-xs text-secondary">Apple Liquid Glass v1.0</span>
            </div>
            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl text-primary">
              Liquid Glass Visual Playground
            </h1>
            <p className="mt-1 text-sm text-secondary">
              Isolated laboratory for validating materials, semantic tokens, theme transitions, and accessibility.
            </p>
          </div>

          {/* Theme Mode Switcher */}
          <GlassSurface variant="floating" className="flex items-center gap-1 p-1.5 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setTheme('light')}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                theme === 'light'
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-secondary hover:text-primary hover:bg-white/10'
              }`}
              title="Activate Light Theme"
            >
              <Sun className="h-3.5 w-3.5" />
              Light
            </button>
            <button
              type="button"
              onClick={() => setTheme('dark')}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                theme === 'dark'
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-secondary hover:text-primary hover:bg-white/10'
              }`}
              title="Activate Dark Theme"
            >
              <Moon className="h-3.5 w-3.5" />
              Dark
            </button>
            <button
              type="button"
              onClick={() => setTheme('system')}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                theme === 'system'
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-secondary hover:text-primary hover:bg-white/10'
              }`}
              title="Follow OS Scheme"
            >
              <Laptop className="h-3.5 w-3.5" />
              System ({resolvedTheme})
            </button>
          </GlassSurface>
        </header>

        {/* System State Banner */}
        <GlassSurface variant="subtle" className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <div>
              <span className="text-xs uppercase tracking-wider text-muted font-mono">Current Theme</span>
              <p className="text-sm font-semibold capitalize text-primary">
                {theme} <span className="text-xs font-normal text-secondary">(Resolved: {resolvedTheme})</span>
              </p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div>
              <span className="text-xs uppercase tracking-wider text-muted font-mono">Backdrop Filter</span>
              <p className="text-sm font-semibold text-status-ok flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" /> Native Hardware Accel
              </p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div>
              <span className="text-xs uppercase tracking-wider text-muted font-mono">Reduced Motion / Fallback</span>
              <p className="text-sm font-medium text-secondary">Supported via @media tokens</p>
            </div>
          </div>
          <button
            type="button"
            onClick={toggleTheme}
            className="flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-primary hover:bg-surface/50 transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Quick Toggle Theme
          </button>
        </GlassSurface>

        {/* Section 1: The Four Glass Material Variants */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-accent" />
            <h2 className="text-xl font-semibold tracking-tight text-primary">Glass Material Variants</h2>
          </div>
          <p className="text-sm text-secondary">
            Hierarchical depth through variable blur, optical saturation, specular borders, and directional drop shadows.
          </p>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {variants.map((v) => (
              <GlassSurface
                key={v.key}
                variant={v.key}
                className={`p-6 transition-all duration-300 ${
                  selectedVariant === v.key ? 'ring-2 ring-accent shadow-xl' : ''
                }`}
                onClick={() => setSelectedVariant(v.key)}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-wider text-accent font-semibold">
                    {v.key}
                  </span>
                  <span className="rounded-full bg-surface/60 px-2 py-0.5 font-mono text-[10px] text-secondary">
                    {v.blur}
                  </span>
                </div>
                <h3 className="mt-3 text-lg font-semibold text-primary">{v.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-secondary">{v.desc}</p>
                <div className="mt-6 pt-4 border-t border-border/50 flex items-center justify-between text-xs">
                  <span className="text-muted font-mono">Class:</span>
                  <code className="text-accent font-mono text-[11px]">.glass-material-{v.key}</code>
                </div>
              </GlassSurface>
            ))}
          </div>
        </section>

        {/* Section 2: Interactive Glass Surfaces & Ambient Glows */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            <h2 className="text-xl font-semibold tracking-tight text-primary">
              Interactive Lift & Ambient Glow Accents
            </h2>
          </div>
          <p className="text-sm text-secondary">
            Interactive surfaces apply subtle specular elevation on hover, tactile depression on active click, and accessible focus rings.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-mono text-secondary">Select Accent Glow:</span>
            {glows.map((g) => (
              <button
                key={g.key}
                type="button"
                onClick={() => setSelectedGlow(g.key)}
                className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all ${
                  selectedGlow === g.key
                    ? 'border-accent bg-accent/15 text-primary shadow-sm'
                    : 'border-border text-secondary hover:text-primary'
                }`}
              >
                <span className={`h-2.5 w-2.5 rounded-full ${g.color}`} />
                {g.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <GlassSurface
              variant="standard"
              interactive
              glow={selectedGlow}
              className="p-6 cursor-pointer"
              onClick={() => setInteractiveCounter((c) => c + 1)}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase text-accent font-semibold">Interactive Card</span>
                <span className="rounded-full bg-accent/20 px-2 py-0.5 font-mono text-xs text-accent">
                  Clicks: {interactiveCounter}
                </span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-primary">Click to Test Surface Reactivity</h3>
              <p className="mt-2 text-xs text-secondary leading-relaxed">
                Applies hover translation `-translate-y-0.5`, ambient shadow bloom, and `role="button"` semantics.
              </p>
              <div className="mt-4 flex items-center gap-2 text-xs font-medium text-accent">
                <span>Trigger Reaction</span>
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
              </div>
            </GlassSurface>

            <GlassSurface variant="floating" glow={selectedGlow} className="p-6">
              <span className="font-mono text-xs uppercase text-accent font-semibold">Live Telemetry Tile</span>
              <h3 className="mt-2 text-base font-semibold text-primary">Induction Motor 04</h3>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono text-primary">1,784</span>
                <span className="text-xs font-mono text-secondary">RPM</span>
                <span className="ml-auto flex items-center gap-1 text-xs font-medium text-status-ok">
                  <Activity className="h-3.5 w-3.5" /> Stable
                </span>
              </div>
              <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-surface">
                <div className="h-full bg-gradient-to-r from-accent to-cyan-400" style={{ width: `${sliderVal}%` }} />
              </div>
            </GlassSurface>

            <GlassSurface variant="modal" glow={selectedGlow} className="p-6">
              <span className="font-mono text-xs uppercase text-accent font-semibold">Modal Depth Simulation</span>
              <h3 className="mt-2 text-base font-semibold text-primary">Isolation & Prominence</h3>
              <p className="mt-2 text-xs text-secondary leading-relaxed">
                Rendered with ~28px multi-layer blur and 210% saturation for high-priority diagnostic alerts.
              </p>
              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white shadow hover:opacity-90 transition-opacity"
                >
                  Confirm Action
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-secondary hover:text-primary transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </GlassSurface>
          </div>
        </section>

        {/* Section 3: Semantic Status Tokens */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-accent" />
            <h2 className="text-xl font-semibold tracking-tight text-primary">
              Semantic Color Palette & Status Indicators
            </h2>
          </div>
          <p className="text-sm text-secondary">
            High-contrast industrial status indicators calibrated for ISO 10816 vibration severity and motor condition telemetry.
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <GlassSurface variant="subtle" className="p-4 border-l-4 border-l-emerald-500">
              <div className="flex items-center gap-2 text-status-ok font-semibold text-sm">
                <CheckCircle2 className="h-4 w-4" />
                <span>Nominal / Healthy</span>
              </div>
              <p className="mt-2 font-mono text-xs text-secondary">Tokens: --status-ok, text-status-ok</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-secondary">Class A/B Zone</span>
                <span className="font-mono text-status-ok font-bold">VIB &lt; 2.8 mm/s</span>
              </div>
            </GlassSurface>

            <GlassSurface variant="subtle" className="p-4 border-l-4 border-l-amber-500">
              <div className="flex items-center gap-2 text-status-warning font-semibold text-sm">
                <AlertTriangle className="h-4 w-4" />
                <span>Warning / Alert</span>
              </div>
              <p className="mt-2 font-mono text-xs text-secondary">Tokens: --status-warning</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-secondary">Class C Zone</span>
                <span className="font-mono text-status-warning font-bold">2.8 - 4.5 mm/s</span>
              </div>
            </GlassSurface>

            <GlassSurface variant="subtle" className="p-4 border-l-4 border-l-rose-500">
              <div className="flex items-center gap-2 text-status-critical font-semibold text-sm">
                <XCircle className="h-4 w-4" />
                <span>Critical / Danger</span>
              </div>
              <p className="mt-2 font-mono text-xs text-secondary">Tokens: --status-critical</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-secondary">Class D Zone</span>
                <span className="font-mono text-status-critical font-bold">VIB &gt; 4.5 mm/s</span>
              </div>
            </GlassSurface>

            <GlassSurface variant="subtle" className="p-4 border-l-4 border-l-blue-500">
              <div className="flex items-center gap-2 text-status-info font-semibold text-sm">
                <Info className="h-4 w-4" />
                <span>Diagnostic Info</span>
              </div>
              <p className="mt-2 font-mono text-xs text-secondary">Tokens: --status-info</p>
              <div className="mt-3 flex items-center justify-between text-xs">
                <span className="text-secondary">Telemetry Sync</span>
                <span className="font-mono text-status-info font-bold">4.2 kS/s</span>
              </div>
            </GlassSurface>
          </div>
        </section>

        {/* Section 4: Glass Form Controls & Sliders */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sliders className="h-5 w-5 text-accent" />
            <h2 className="text-xl font-semibold tracking-tight text-primary">Glass Form Controls & Inputs</h2>
          </div>
          <p className="text-sm text-secondary">
            Form controls with translucent inner specular highlights and focus ring tokens.
          </p>

          <GlassSurface variant="standard" className="p-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <label htmlFor="equipment-name-input" className="block text-xs font-mono font-medium text-secondary mb-1.5">
                  Equipment Asset Identifier
                </label>
                <input
                  id="equipment-name-input"
                  type="text"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface/50 px-3.5 py-2 text-sm text-primary placeholder-muted outline-none transition-all focus:border-accent focus:ring-2 focus:ring-accent/30"
                />
              </div>

              <div>
                <label htmlFor="diagnostic-mode-select" className="block text-xs font-mono font-medium text-secondary mb-1.5">
                  Diagnostic Sensitivity
                </label>
                <select
                  id="diagnostic-mode-select"
                  className="w-full rounded-lg border border-border bg-surface/50 px-3.5 py-2 text-sm text-primary outline-none transition-all focus:border-accent focus:ring-2 focus:ring-accent/30"
                >
                  <option value="balanced" className="bg-canvas text-primary">Balanced Precision</option>
                  <option value="high" className="bg-canvas text-primary">High-Frequency Vibration Detection</option>
                  <option value="thermal" className="bg-canvas text-primary">Thermal Baseline Drift</option>
                </select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="threshold-range-slider" className="text-xs font-mono font-medium text-secondary">
                    Anomaly Threshold
                  </label>
                  <span className="font-mono text-xs font-semibold text-accent">{sliderVal}%</span>
                </div>
                <input
                  id="threshold-range-slider"
                  type="range"
                  min="0"
                  max="100"
                  value={sliderVal}
                  onChange={(e) => setSliderVal(Number(e.target.value))}
                  className="w-full accent-accent cursor-pointer"
                />
              </div>
            </div>
          </GlassSurface>
        </section>

        {/* Section 5: Specification & Token Matrix */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-accent" />
            <h2 className="text-xl font-semibold tracking-tight text-primary">
              Token Architecture & CSS Specification
            </h2>
          </div>

          <div className="overflow-x-auto">
            <GlassSurface variant="subtle" className="p-4">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-border text-secondary">
                    <th className="pb-2">Token Name</th>
                    <th className="pb-2">Light Theme Value</th>
                    <th className="pb-2">Dark Theme Value</th>
                    <th className="pb-2">Role / Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-primary">
                  <tr>
                    <td className="py-2.5 text-accent">--bg-canvas</td>
                    <td className="py-2.5">#F3F6FA</td>
                    <td className="py-2.5">#080D16</td>
                    <td className="py-2.5 text-secondary">Deep canvas underlay</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-accent">--bg-surface</td>
                    <td className="py-2.5">#FFFFFF</td>
                    <td className="py-2.5">#151E2C</td>
                    <td className="py-2.5 text-secondary">Solid base surface</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-accent">--bg-raised</td>
                    <td className="py-2.5">#E5EBF3</td>
                    <td className="py-2.5">#253348</td>
                    <td className="py-2.5 text-secondary">Elevated container backgrounds</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-accent">--text-primary</td>
                    <td className="py-2.5">#182333</td>
                    <td className="py-2.5">#F2F6FC</td>
                    <td className="py-2.5 text-secondary">Primary legible typography</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-accent">--accent</td>
                    <td className="py-2.5">#286CC4</td>
                    <td className="py-2.5">#83B9FF</td>
                    <td className="py-2.5 text-secondary">Action accent & focus rings</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-accent">--glass-blur-standard</td>
                    <td className="py-2.5" colSpan={2}>16px</td>
                    <td className="py-2.5 text-secondary">Standard panel glass diffusion</td>
                  </tr>
                </tbody>
              </table>
            </GlassSurface>
          </div>
        </section>
      </div>
    </div>
  )
}

export default DesignPlaygroundPage
