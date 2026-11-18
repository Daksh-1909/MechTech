import { Activity, ArrowRight, BrainCircuit, Gauge, Radio, ShieldCheck, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { IntroOverlay } from '../components/IntroOverlay'

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
    <div className="landing-page min-h-screen overflow-hidden bg-canvas text-primary">
      <IntroOverlay />
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="MechTech home">
          <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-black">
            <Activity className="size-6" />
          </span>
          <span>
            <span className="block text-lg font-bold tracking-tight">MechTech</span>
            <span className="block font-mono text-[10px] tracking-[0.2em] text-slate-400 uppercase">
              Equipment intelligence
            </span>
          </span>
        </Link>
        <nav className="flex items-center gap-3" aria-label="Main navigation">
          <a
            href="#platform"
            className="hidden px-3 py-2 text-sm text-slate-300 hover:text-white sm:inline"
          >
            Platform
          </a>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="magnetic-control inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-accent-hover"
            >
              Open workspace <ArrowRight className="size-4" />
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-white/5"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="rounded-lg border border-accent/50 bg-accent/10 px-4 py-2.5 text-sm font-semibold text-accent transition hover:bg-accent/20"
              >
                Request access
              </Link>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 pt-14 pb-20 sm:px-8 sm:pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pt-24 lg:pb-28">
          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1.5 font-mono text-[11px] tracking-[0.14em] text-accent uppercase">
              <span className="size-1.5 rounded-full bg-accent" />
              Condition monitoring for electric motors
            </div>
            <h1 className="max-w-3xl text-4xl leading-[1.08] font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Keep critical equipment <span className="text-accent">in view.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              MechTech brings motor telemetry, anomaly signals, diagnostic evidence, and maintenance
              history into one clear workspace.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="magnetic-control inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-black transition"
                >
                  Go to workspace <ArrowRight className="size-4" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    className="magnetic-control inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-black transition"
                  >
                    Request an account <ArrowRight className="size-4" />
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-white/5"
                  >
                    Sign in to your workspace
                  </Link>
                </>
              )}
            </div>
            {!isAuthenticated && (
              <p className="mt-4 max-w-lg text-xs leading-5 text-slate-500">
                Workspace access requires an account. New registrations are reviewed by an
                administrator before sign-in is enabled.
              </p>
            )}
            <div className="mt-10 flex items-center gap-3 border-t border-slate-800 pt-6 text-xs text-slate-400">
              <ShieldCheck className="size-4 text-emerald-300" />
              <span>Role-protected workspace with traceable advisory results</span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl">
          <div className="absolute -inset-6 rounded-[2rem]" />
            <div className="relative rounded-2xl border border-slate-700/80 bg-slate-900/90 p-4 shadow-2xl shadow-black/40 backdrop-blur sm:p-5">
              <div className="flex items-center justify-between border-b border-slate-800 px-1 pb-4">
                <div>
                  <p className="font-mono text-[10px] tracking-[0.18em] text-slate-500 uppercase">
                    Fleet snapshot
                  </p>
                  <h2 className="mt-1 text-sm font-semibold text-white">
                    Motor condition overview
                  </h2>
                </div>
                <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-2.5 py-1 font-mono text-[10px] text-emerald-200">
                  <span className="size-1.5 rounded-full bg-emerald-300" /> MONITORING
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs">Equipment status</span>
                    <Gauge className="size-4 text-cyan-300" />
                  </div>
                  <p className="mt-3 text-2xl font-semibold text-white">In view</p>
                  <p className="mt-1 text-[11px] text-slate-500">Telemetry and event history</p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs">Analysis</span>
                    <BrainCircuit className="size-4 text-violet-300" />
                  </div>
                  <p className="mt-3 text-2xl font-semibold text-white">Traceable</p>
                  <p className="mt-1 text-[11px] text-slate-500">Evidence linked to each result</p>
                </div>
              </div>
              <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-200">Sensor stream</p>
                    <p className="mt-1 text-[10px] text-slate-500">
                      Temperature · vibration · operating conditions
                    </p>
                  </div>
                  <Activity className="size-4 text-cyan-300" />
                </div>
                <div className="mt-5 flex h-20 items-end gap-1.5" aria-hidden="true">
                  {[
                    36, 48, 42, 58, 51, 67, 55, 72, 61, 78, 69, 84, 73, 89, 77, 95, 82, 74, 88, 79,
                    92, 70, 81, 68,
                  ].map((height, index) => (
                    <span
                      key={index}
                      className="flex-1 rounded-t-sm bg-accent/70"
                      style={{ height: `${height}%` }}
                    />
                  ))}
                </div>
                <div className="mt-2 flex justify-between font-mono text-[9px] text-slate-600">
                  <span>EARLIER</span>
                  <span>RECENT</span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-3 rounded-xl border border-amber-400/20 bg-amber-400/5 p-3.5">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-amber-400/10 text-amber-200">
                  <Activity className="size-4" />
                </span>
                <div>
                  <p className="text-xs font-medium text-amber-100">
                    Review results with their evidence
                  </p>
                  <p className="mt-1 text-[10px] leading-4 text-slate-400">
                    Predictions are advisory and require human review.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="platform" className="border-y border-slate-800/80 bg-slate-900/35">
          <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:py-20">
            <div className="max-w-2xl">
              <p className="font-mono text-[11px] tracking-[0.18em] text-cyan-300 uppercase">
                One equipment workspace
              </p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                From incoming readings to informed maintenance
              </h2>
              <p className="mt-4 text-sm leading-6 text-slate-400">
                Follow equipment signals through monitoring, diagnostics, and service history
                without losing the context behind a result.
              </p>
            </div>
            <div className="mt-9 grid gap-4 md:grid-cols-3">
              {capabilities.map(({ icon: Icon, title, description }) => (
                <article
                  key={title}
                  className="rounded-xl border border-slate-800 bg-slate-950/65 p-5"
                >
                  <span className="flex size-10 items-center justify-center rounded-lg border border-cyan-300/15 bg-cyan-300/5 text-cyan-200">
                    <Icon className="size-5" />
                  </span>
                  <h3 className="mt-4 text-sm font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <span>MechTech · Detect. Diagnose. Maintain.</span>
        <span>Monitoring and model outputs are advisory; verify equipment in person.</span>
      </footer>
    </div>
  )
}

export default LandingPage
