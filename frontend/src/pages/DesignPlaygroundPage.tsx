import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Activity, ArrowRight, Gauge, Layers, Moon, Sun, Laptop, Waves } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

const spring = { type: 'spring' as const, stiffness: 420, damping: 30, mass: 0.7 }

export default function DesignPlaygroundPage() {
  const { theme, resolvedTheme, setTheme } = useTheme()
  const [active, setActive] = useState('Materials')
  const reduceMotion = useReducedMotion()
  const tabs = ['Materials', 'Motion', 'Telemetry']
  return <main className="playground mx-auto min-h-screen max-w-6xl space-y-10 px-5 py-8 sm:px-8">
    <header className="flex flex-wrap items-end justify-between gap-6">
      <div><p className="font-mono text-xs uppercase tracking-[.18em] text-accent">MechTech / Design system</p><h1 className="mt-3 text-4xl font-medium tracking-tight text-primary sm:text-5xl">Liquid, with restraint.</h1><p className="mt-3 max-w-xl text-sm leading-6 text-secondary">A monochrome engineering interface with layered glass, elastic selection, and a single signal color.</p></div>
      <div className="glass-material-floating flex rounded-lg border border-border p-1" role="group" aria-label="Color theme">
        {([{ id: 'light', Icon: Sun }, { id: 'dark', Icon: Moon }, { id: 'system', Icon: Laptop }] as const).map(({ id, Icon }) => <button key={id} type="button" onClick={() => setTheme(id)} aria-pressed={theme === id} className="relative flex items-center gap-2 rounded-md px-3 py-2 text-xs capitalize text-secondary focus-visible:outline-accent">
          {theme === id && <motion.span layoutId="theme-indicator" className="absolute inset-0 rounded-md bg-accent/15" transition={reduceMotion ? { duration: 0 } : spring} />}
          <Icon className="relative size-3.5"/><span className="relative">{id}</span>
        </button>)}
      </div>
    </header>

    <section className="grid gap-5 lg:grid-cols-[1.35fr_.65fr]">
      <div className="playground-stage relative overflow-hidden rounded-xl border border-border p-6 sm:p-9">
        <div className="relative z-10 flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-[10px] uppercase tracking-[.16em] text-muted">Interactive preview / {resolvedTheme} mode</p><h2 className="mt-2 text-xl font-medium">Surface behavior</h2></div><span className="rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 font-mono text-[10px] text-accent">SIGNAL / 01</span></div>
        <div className="relative z-10 mt-7 grid gap-4 sm:grid-cols-2">
          <article className="glass-panel p-5"><div className="flex justify-between"><span className="font-mono text-[10px] text-muted">MOTOR / A-102</span><Activity className="size-4 text-accent"/></div><p className="mt-7 font-mono text-4xl tabular-nums">1,482<span className="ml-2 text-sm text-secondary">rpm</span></p><p className="mt-1 text-xs text-secondary">Shaft rotation · nominal</p><div className="mt-5 flex h-12 items-end gap-1" aria-label="Static sample telemetry"><span className="telemetry-bar h-4"/><span className="telemetry-bar h-7"/><span className="telemetry-bar h-5"/><span className="telemetry-bar h-9"/><span className="telemetry-bar h-6"/><span className="telemetry-bar h-11"/><span className="telemetry-bar h-8"/><span className="telemetry-bar h-10"/></div></article>
          <article className="glass-panel flex flex-col justify-between p-5"><div className="flex justify-between"><span className="font-mono text-[10px] text-muted">CONDITION</span><Gauge className="size-4 text-secondary"/></div><div><p className="mt-6 text-2xl font-medium">Within range</p><p className="mt-2 text-xs text-secondary">Vibration and temperature stable.</p></div><div className="mt-5 h-1 overflow-hidden rounded-full bg-raised"><div className="h-full w-[72%] rounded-full bg-accent"/></div></article>
        </div>
        <p className="relative z-10 mt-5 font-mono text-[10px] text-muted">TRANSLUCENCY · EDGE REFLECTION · LAYERED DEPTH</p>
      </div>
      <aside className="glass-material-standard rounded-xl border border-border p-6"><div className="flex items-center gap-2 text-accent"><Layers className="size-4"/><h2 className="text-sm font-medium text-primary">Palette & material</h2></div><div className="mt-5 space-y-3">{[['White','#FFFFFF','swatch-white'],['Matte Black','#000000','swatch-black'],['Signal Orange','#FF5A36','swatch-orange']].map(([name,hex,cls])=><div key={name} className="flex items-center gap-3"><span className={`h-9 w-9 rounded-md border border-border ${cls}`}/><span className="text-xs text-primary">{name}</span><code className="ml-auto font-mono text-[10px] text-muted">{hex}</code></div>)}</div><div className="mt-6 border-t border-border pt-5"><p className="font-mono text-[10px] uppercase tracking-wider text-muted">Current theme</p><p className="mt-2 text-sm capitalize">{theme} <span className="text-secondary">· resolved {resolvedTheme}</span></p></div></aside>
    </section>

    <section className="space-y-4"><div><p className="font-mono text-[10px] uppercase tracking-[.16em] text-muted">Elastic selection / reduced motion: {reduceMotion ? 'on' : 'off'}</p><h2 className="mt-1 text-xl font-medium">Shared active surface</h2></div>
      <div className="glass-material-subtle relative inline-flex rounded-lg border border-border p-1" role="tablist" aria-label="Preview panels">{tabs.map(tab=><button key={tab} role="tab" aria-selected={active===tab} onClick={()=>setActive(tab)} className="relative rounded-md px-4 py-2 text-xs text-secondary focus-visible:outline-accent">{active===tab&&<motion.span layoutId="playground-tab" className="absolute inset-0 rounded-md border border-white/10 bg-accent/15 shadow-sm" transition={reduceMotion?{duration:0}:spring}/>}<span className="relative">{tab}</span></button>)}</div>
      <div className="glass-panel min-h-40 max-w-3xl p-6" role="tabpanel"><motion.div key={active} initial={reduceMotion?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.22}}><div className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-md bg-accent/10 text-accent"><Waves className="size-4"/></span><div><h3 className="text-sm font-medium">{active} transition</h3><p className="mt-1 text-xs text-secondary">The selection stretches into place and settles with a damped spring.</p></div></div><button className="magnetic-control glass-btn glass-btn-primary mt-5" onPointerMove={event=>{if(reduceMotion)return;const r=event.currentTarget.getBoundingClientRect();event.currentTarget.style.transform=`translate(${(event.clientX-r.left-r.width/2)*.08}px, ${(event.clientY-r.top-r.height/2)*.08}px)`}} onPointerLeave={event=>{event.currentTarget.style.transform='translate(0,0)'}}><span>Explore workspace</span><ArrowRight className="size-3.5"/></button></motion.div></div>
    </section>
  </main>
}
