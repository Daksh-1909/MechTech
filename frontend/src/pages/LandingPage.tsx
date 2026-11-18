import { Activity, ArrowRight, BrainCircuit, Gauge, Radio, ShieldCheck, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { IntroOverlay } from '../components/IntroOverlay'
import { BackgroundPaths } from '../components/ui/BackgroundPaths'
import { MagneticControl } from '../components/glass/MagneticControl'

const capabilities = [
  {
    icon: Radio,
    title: 'Live equipment telemetry',
    description: 'Review sensor readings, operating status, and changes across your motor fleet.',
  },
  {
    icon: BrainCircuit,
    title: 'Evidence-backed diagnostics',
    description:
      'See anomaly signals and advisory fault classifications with their supporting evidence.',
  },
  {
    icon: Wrench,
    title: 'Maintenance in context',
    description: 'Connect alerts and equipment history to maintenance work and follow-up.',
  },
]

export const LandingPage = () => {
  const { isAuthenticated } = useAuth()

  return (
    <div className="landing-page relative min-h-screen overflow-x-hidden bg-white text-[#171717]">
      <IntroOverlay />

      {/* UI Hub Floating Curved Lines Background — Full-Viewport Fluid Motion */}
      <div
        className="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none"
        aria-hidden="true"
        style={{ contain: 'strict', transform: 'translateZ(0)' }}
      >
        <BackgroundPaths
          pathColor="#171717"
          accentColor="#FF5A36"
          className="h-full w-full bg-transparent"
          opacity={1}
        />
      </div>

      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="MechTech home">
          <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-white shadow-sm">
            <Activity className="size-6 text-white" />
          </span>
          <span>
            <span className="block text-lg font-bold tracking-tight text-[#171717]">MechTech</span>
            <span className="block font-mono text-[10px] tracking-[0.2em] text-[#171717]/60 uppercase">
              Equipment intelligence
            </span>
          </span>
        </Link>
        <nav className="flex items-center gap-3" aria-label="Main navigation">
          <a
            href="#platform"
            className="hidden px-3 py-2 text-sm text-[#171717]/75 hover:text-[#171717] sm:inline transition-colors font-medium"
          >
            Platform
          </a>
          <Link
            to="/design-system"
            className="hidden px-3 py-2 text-sm text-[#171717]/75 hover:text-[#171717] sm:inline transition-colors font-medium"
          >
            Design System
          </Link>
          {isAuthenticated ? (
            <MagneticControl>
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-hover shadow-sm"
              >
                Open workspace <ArrowRight className="size-4" />
              </Link>
            </MagneticControl>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-lg px-3 py-2 text-sm text-[#171717]/80 hover:text-[#171717] hover:bg-black/5 transition-colors font-medium"
              >
                Sign in
              </Link>
              <MagneticControl>
                <Link
                  to="/register"
                  className="rounded-lg border border-accent bg-accent/10 px-4 py-2.5 text-sm font-semibold text-accent transition hover:bg-accent hover:text-white"
                >
                  Request access
                </Link>
              </MagneticControl>
            </>
          )}
        </nav>
      </header>

      <main className="relative z-10">
        <section className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 pt-14 pb-20 sm:px-8 sm:pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pt-24 lg:pb-28">
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3.5 py-1.5 font-mono text-[11px] tracking-[0.14em] text-accent uppercase font-semibold">
              <span className="size-1.5 rounded-full bg-accent" />
              Condition monitoring for electric motors
            </div>
            <h1 className="max-w-3xl text-4xl leading-[1.08] font-bold tracking-tight text-[#171717] sm:text-5xl lg:text-6xl">
              Keep critical equipment <span className="text-accent">in view.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-[#171717]/80 sm:text-lg">
              MechTech brings motor telemetry, anomaly signals, diagnostic evidence, and maintenance
              history into one clean monochrome liquid glass workspace.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              {isAuthenticated ? (
                <MagneticControl>
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-hover shadow-sm"
                  >
                    Go to workspace <ArrowRight className="size-4" />
                  </Link>
                </MagneticControl>
              ) : (
                <>
                  <MagneticControl>
                    <Link
                      to="/register"
                      className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-hover shadow-sm"
                    >
                      Request an account <ArrowRight className="size-4" />
                    </Link>
                  </MagneticControl>
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center rounded-lg border border-black/15 bg-white/70 px-5 py-3 text-sm font-semibold text-[#171717] backdrop-blur-md transition hover:border-black/40 hover:bg-white"
                  >
                    Sign in to your workspace
                  </Link>
                </>
              )}
            </div>
            {!isAuthenticated && (
              <p className="mt-4 max-w-lg text-xs leading-5 text-[#171717]/60 font-mono">
                Workspace access requires an account. New registrations are reviewed by an
                administrator before sign-in is enabled.
              </p>
            )}
            <div className="mt-10 flex items-center gap-3 border-t border-black/10 pt-6 text-xs text-[#171717]/70 font-mono">
              <ShieldCheck className="size-4 text-accent" />
              <span>Role-protected workspace with traceable advisory results</span>
            </div>
          </div>

          {/* Liquid Glass Preview Card — Translucent, showing moving vector curves underneath */}
          <div className="relative mx-auto w-full max-w-xl">
            <div className="relative rounded-2xl border border-black/12 bg-white/80 p-5 shadow-2xl backdrop-blur-2xl sm:p-6">
              <div className="flex items-center justify-between border-b border-black/10 px-1 pb-4">
                <div>
                  <p className="font-mono text-[10px] tracking-[0.18em] text-[#171717]/50 uppercase">
                    Fleet snapshot
                  </p>
                  <h2 className="mt-1 text-sm font-bold text-[#171717]">
                    Motor condition overview
                  </h2>
                </div>
                <span className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-2.5 py-1 font-mono text-[10px] text-accent font-semibold">
                  <span className="size-1.5 rounded-full bg-accent animate-pulse" /> MONITORING
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-black/8 bg-white/60 p-4 backdrop-blur-md">
                  <div className="flex items-center justify-between text-[#171717]/70">
                    <span className="text-xs font-medium">Equipment status</span>
                    <Gauge className="size-4 text-accent" />
                  </div>
                  <p className="mt-3 text-2xl font-bold text-[#171717]">In view</p>
                  <p className="mt-1 text-[11px] text-[#171717]/50">Telemetry and event history</p>
                </div>
                <div className="rounded-xl border border-black/8 bg-white/60 p-4 backdrop-blur-md">
                  <div className="flex items-center justify-between text-[#171717]/70">
                    <span className="text-xs font-medium">Analysis</span>
                    <BrainCircuit className="size-4 text-[#171717]/70" />
                  </div>
                  <p className="mt-3 text-2xl font-bold text-[#171717]">Traceable</p>
                  <p className="mt-1 text-[11px] text-[#171717]/50">Evidence linked to each result</p>
                </div>
              </div>
              <div className="mt-3 rounded-xl border border-black/8 bg-white/60 p-4 backdrop-blur-md">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-[#171717]">Sensor stream</p>
                    <p className="mt-1 text-[10px] text-[#171717]/50">
                      Temperature · vibration · operating conditions
                    </p>
                  </div>
                  <Activity className="size-4 text-accent" />
                </div>
                <div className="mt-5 flex h-20 items-end gap-1.5" aria-hidden="true">
                  {[
                    36, 48, 42, 58, 51, 67, 55, 72, 61, 78, 69, 84, 73, 89, 77, 95, 82, 74, 88, 79,
                    92, 70, 81, 68,
                  ].map((height, index) => (
                    <span
                      key={index}
                      className="flex-1 rounded-t-sm bg-accent/80"
                      style={{ height: `${height}%` }}
                    />
                  ))}
                </div>
                <div className="mt-2 flex justify-between font-mono text-[9px] text-[#171717]/50">
                  <span>EARLIER</span>
                  <span>RECENT</span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3 rounded-xl border border-accent/30 bg-accent/5 p-3.5 backdrop-blur-md">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                  <Activity className="size-4" />
                </span>
                <div>
                  <p className="text-xs font-semibold text-[#171717]">
                    Review results with their evidence
                  </p>
                  <p className="mt-1 text-[10px] leading-4 text-[#171717]/70">
                    Predictions are advisory and require human review.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="platform" className="border-y border-black/10 bg-white/70 backdrop-blur-xl">
          <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:py-20">
            <div className="max-w-2xl">
              <p className="font-mono text-[11px] tracking-[0.18em] text-accent uppercase font-semibold">
                One equipment workspace
              </p>
              <h2 className="mt-3 text-2xl font-bold tracking-tight text-[#171717] sm:text-3xl">
                From incoming readings to informed maintenance
              </h2>
              <p className="mt-4 text-sm leading-6 text-[#171717]/75">
                Follow equipment signals through monitoring, diagnostics, and service history
                without losing the context behind a result.
              </p>
            </div>
            <div className="mt-9 grid gap-4 md:grid-cols-3">
              {capabilities.map(({ icon: Icon, title, description }) => (
                <article
                  key={title}
                  className="rounded-xl border border-black/10 bg-white/80 p-5 shadow-sm backdrop-blur-lg transition-transform hover:-translate-y-1"
                >
                  <span className="flex size-10 items-center justify-center rounded-lg border border-accent/30 bg-accent/10 text-accent">
                    <Icon className="size-5" />
                  </span>
                  <h3 className="mt-4 text-sm font-bold text-[#171717]">{title}</h3>
                  <p className="mt-2 text-xs leading-5 text-[#171717]/70">{description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-[#171717]/60 sm:flex-row sm:items-center sm:justify-between sm:px-8 font-mono">
        <span>MechTech · Detect. Diagnose. Maintain.</span>
        <span>Monitoring and model outputs are advisory; verify equipment in person.</span>
      </footer>
    </div>
  )
}

export default LandingPage
