import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  Clock3,
  Film,
  Play,
  Rocket,
  ShieldCheck,
  Sparkles,
  Upload,
  Wand2,
} from 'lucide-react';
import heroPoster from '../assets/hero.png';

const pipelineSteps = [
  {
    icon: Upload,
    step: '01',
    title: 'Drop Full Tour',
    desc: 'Upload one long property walkthrough or paste a YouTube tour link.',
  },
  {
    icon: Wand2,
    step: '02',
    title: 'AI Finds Peak Moments',
    desc: 'Scene detection extracts the strongest non-overlapping highlights automatically.',
  },
  {
    icon: Film,
    step: '03',
    title: 'Story & Style Auto-Built',
    desc: 'The timeline is sequenced into a clean real-estate narrative with cinematic pacing.',
  },
  {
    icon: Rocket,
    step: '04',
    title: 'Export Reels Instantly',
    desc: 'Get social-ready shorts with hooks, transitions, and optimized aspect ratios.',
  },
];

const statCards = [
  { label: 'Manual Editing Saved', value: '8-12 hrs/listing' },
  { label: 'Typical Output Time', value: '< 5 mins' },
  { label: 'Reel Variations', value: '3 per render' },
];

const trustPoints = [
  { icon: ShieldCheck, text: 'Built-in quality checks before delivery' },
  { icon: Clock3, text: 'Progressive pipeline with render audit logs' },
  { icon: BarChart3, text: 'Coverage analytics on every generated timeline' },
];

const logoPills = ['PrimeNest', 'UrbanDwell', 'Skyline Group', 'Habitat Studio', 'VillaWorks'];

const testimonials = [
  {
    quote: 'We moved from manual timeline edits to one-click reels for every listing.',
    name: 'Ananya Rao',
    role: 'Broker, PrimeNest',
  },
  {
    quote: 'The AI picks better hooks than our old editing workflow and saves us hours.',
    name: 'Karthik Mehta',
    role: 'Marketing Lead, UrbanDwell',
  },
];

const heroPipelineStatus = [
  { icon: Upload, label: 'Upload Validated', detail: '1 home tour, 18m 42s', progress: 100 },
  { icon: Wand2, label: 'Scene AI Pass', detail: '24 highlight windows detected', progress: 82 },
  { icon: Film, label: 'Story Sequencing', detail: 'Luxury narrative assembled', progress: 64 },
  { icon: Rocket, label: 'Reel Export', detail: 'Vertical variants preparing', progress: 38 },
];

const ease = [0.22, 1, 0.36, 1];

export default function LandingPage() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className="min-h-screen bg-[#f6f8ff] pb-24 text-[#0f172a] font-['Manrope'] selection:bg-[#16a34a]/20 overflow-hidden sm:pb-0">
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-44 -left-24 h-[32rem] w-[32rem] rounded-full bg-[#0ea5e9]/20 blur-[120px]" />
        <div className="absolute top-[18%] -right-20 h-[26rem] w-[26rem] rounded-full bg-[#14b8a6]/18 blur-[120px]" />
        <div className="absolute bottom-[-12rem] left-1/3 h-[24rem] w-[24rem] rounded-full bg-[#f97316]/14 blur-[130px]" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(15,23,42,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.03)_1px,transparent_1px)] bg-[size:42px_42px]" />
      </div>

      <header className="relative z-10">
        <nav className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-[#0ea5e9] via-[#06b6d4] to-[#14b8a6] shadow-[0_18px_40px_rgba(14,165,233,0.35)]">
              <Play size={18} className="ml-0.5 text-white" fill="white" />
            </div>
            <span className="font-['Sora'] text-2xl font-extrabold tracking-tight">ReelForge</span>
          </Link>

          <div className="hidden items-center gap-8 text-sm font-bold text-[#334155] md:flex">
            <a href="#workflow" className="transition hover:text-[#0ea5e9]">Workflow</a>
            <a href="#results" className="transition hover:text-[#0ea5e9]">Results</a>
            <a href="#pricing" className="transition hover:text-[#0ea5e9]">Pricing</a>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/login" className="hidden rounded-xl px-4 py-2 text-sm font-bold text-[#475569] transition hover:bg-white/70 sm:inline-flex">
              Sign In
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 rounded-xl bg-[#0f172a] px-5 py-2.5 text-sm font-extrabold text-white shadow-[0_14px_34px_rgba(15,23,42,0.25)] transition hover:-translate-y-0.5 hover:bg-[#1e293b]"
            >
              Start Free
              <ArrowRight size={16} />
            </Link>
          </div>
        </nav>
      </header>

      <main className="relative z-10">
        <section className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-12 px-6 pb-24 pt-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-10 lg:pb-28 lg:pt-12">
          <div>
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease }}
              className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#dbeafe] bg-white/80 px-4 py-2 text-xs font-extrabold uppercase tracking-[0.14em] text-[#0369a1] backdrop-blur"
            >
              <Sparkles size={14} />
              AI Reel Studio For Real Estate
            </motion.div>

            <motion.h1
              initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
              className="font-['Sora'] text-5xl font-extrabold leading-[1.04] tracking-[-0.03em] text-[#020617] sm:text-6xl lg:text-7xl"
            >
              From One Home Tour
              <span className="block bg-gradient-to-r from-[#0ea5e9] via-[#06b6d4] to-[#14b8a6] bg-clip-text text-transparent">
                To Scroll-Stopping Reels
              </span>
            </motion.h1>

            <motion.p
              initial={prefersReducedMotion ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.55, delay: prefersReducedMotion ? 0 : 0.2 }}
              className="mt-6 max-w-2xl text-lg font-medium leading-relaxed text-[#475569]"
            >
              Upload raw footage or paste a YouTube property tour. ReelForge isolates the best scenes, builds narrative flow, and renders polished shorts for Reels, TikTok, and YouTube.
            </motion.p>

            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: prefersReducedMotion ? 0 : 0.28 }}
              className="mt-9 flex flex-col gap-4 sm:flex-row"
            >
              <Link
                to="/signup"
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-[#0ea5e9] via-[#06b6d4] to-[#14b8a6] px-7 py-4 text-base font-extrabold text-white shadow-[0_24px_44px_rgba(14,165,233,0.35)] transition hover:-translate-y-0.5"
              >
                Build My First Reel
                <ArrowRight size={18} />
              </Link>
              <a
                href="#workflow"
                className="inline-flex items-center justify-center rounded-2xl border-2 border-[#dbe3f1] bg-white/80 px-7 py-4 text-base font-extrabold text-[#0f172a] backdrop-blur transition hover:border-[#0ea5e9]/50"
              >
                See Pipeline
              </a>
            </motion.div>

            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: prefersReducedMotion ? 0 : 0.36 }}
              className="mt-10 grid gap-3 sm:grid-cols-3"
            >
              {statCards.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-[#e2e8f0] bg-white/80 px-4 py-4 backdrop-blur">
                  <p className="font-['Sora'] text-xl font-bold tracking-tight text-[#0f172a]">{stat.value}</p>
                  <p className="mt-1 text-xs font-extrabold uppercase tracking-[0.1em] text-[#64748b]">{stat.label}</p>
                </div>
              ))}
            </motion.div>
          </div>

          <motion.div
            initial={prefersReducedMotion ? false : { opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.7, ease, delay: prefersReducedMotion ? 0 : 0.15 }}
            className="relative mx-auto w-full max-w-[560px]"
          >
            <div className="absolute -inset-6 rounded-[2.2rem] bg-gradient-to-br from-[#0ea5e9]/20 to-[#14b8a6]/20 blur-2xl" />

            <div className="relative rounded-[2rem] border border-white/60 bg-white/70 p-4 shadow-[0_40px_80px_rgba(15,23,42,0.16)] backdrop-blur-xl">
              <div className="mb-4 rounded-2xl border border-[#dbe3f1] bg-[#f8fbff] px-4 py-3">
                <div>
                  <p className="font-['Sora'] text-sm font-bold tracking-tight text-[#0f172a]">Cinematic Preview</p>
                  <p className="text-xs font-bold uppercase tracking-[0.08em] text-[#64748b]">Upload to final export workflow</p>
                </div>
              </div>

              <div className="relative mx-auto w-full max-w-[460px] overflow-hidden rounded-[1.5rem] border border-[#d6deeb] bg-[#020617] p-4">
                <div className="pointer-events-none absolute -right-12 -top-14 h-40 w-40 rounded-full bg-[#22d3ee]/25 blur-3xl" />
                <div className="pointer-events-none absolute -bottom-16 -left-8 h-40 w-40 rounded-full bg-[#14b8a6]/20 blur-3xl" />

                <div className="relative mb-3 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <div>
                    <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-[#7dd3fc]">Realtime Pipeline</p>
                    <p className="mt-1 text-sm font-bold text-white">Full-Tour Ingestion Health</p>
                  </div>
                  <span className="rounded-full border border-[#22d3ee]/40 bg-[#22d3ee]/15 px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#67e8f9]">
                    Live
                  </span>
                </div>

                <div className="space-y-2.5">
                  {heroPipelineStatus.map((item, index) => (
                    <motion.div
                      key={item.label}
                      initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, ease, delay: prefersReducedMotion ? 0 : 0.12 + index * 0.06 }}
                      className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2.5"
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg border border-[#67e8f9]/30 bg-[#22d3ee]/15 text-[#67e8f9]">
                          <item.icon size={14} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <p className="truncate text-xs font-extrabold uppercase tracking-[0.08em] text-white/95">{item.label}</p>
                            <p className="text-[10px] font-bold text-[#a5f3fc]">{item.progress}%</p>
                          </div>
                          <p className="mt-0.5 truncate text-[11px] font-semibold text-[#cbd5e1]">{item.detail}</p>
                          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/15">
                            <motion.div
                              initial={prefersReducedMotion ? false : { width: 0 }}
                              animate={{ width: `${item.progress}%` }}
                              transition={{ duration: 0.8, ease, delay: prefersReducedMotion ? 0 : 0.2 + index * 0.06 }}
                              className="h-full rounded-full bg-gradient-to-r from-[#22d3ee] to-[#14b8a6]"
                            />
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="mt-3 grid grid-cols-3 gap-2">
                  <div className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-2 text-center">
                    <p className="text-xs font-extrabold text-white">24</p>
                    <p className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#94a3b8]">Scenes</p>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-2 text-center">
                    <p className="text-xs font-extrabold text-white">3</p>
                    <p className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#94a3b8]">Variants</p>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-2 text-center">
                    <p className="text-xs font-extrabold text-white">9:16</p>
                    <p className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#94a3b8]">Ratio</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-3">
                <div className="rounded-xl border border-[#dbe3f1] bg-white px-3 py-3 text-center">
                  <p className="font-['Sora'] text-base font-bold text-[#0f172a]">9:16</p>
                  <p className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#64748b]">Reels</p>
                </div>
                <div className="rounded-xl border border-[#dbe3f1] bg-white px-3 py-3 text-center">
                  <p className="font-['Sora'] text-base font-bold text-[#0f172a]">3 Styles</p>
                  <p className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#64748b]">Luxury/Viral</p>
                </div>
                <div className="rounded-xl border border-[#dbe3f1] bg-white px-3 py-3 text-center">
                  <p className="font-['Sora'] text-base font-bold text-[#0f172a]">Audit</p>
                  <p className="text-[10px] font-extrabold uppercase tracking-[0.08em] text-[#64748b]">Render pass</p>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        <section className="mx-auto w-full max-w-7xl px-6 pb-10 lg:px-10">
          <motion.div
            initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.5, ease }}
            className="rounded-[1.6rem] border border-[#dbe3f1] bg-white/80 px-6 py-6 backdrop-blur"
          >
            <p className="text-center text-xs font-extrabold uppercase tracking-[0.12em] text-[#64748b]">
              Trusted By Fast-Moving Property Teams
            </p>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
              {logoPills.map((logo) => (
                <div key={logo} className="inline-flex items-center gap-2 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-2">
                  <Building2 size={14} className="text-[#0ea5e9]" />
                  <span className="text-sm font-extrabold text-[#334155]">{logo}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </section>

        <section id="workflow" className="mx-auto w-full max-w-7xl px-6 py-20 lg:px-10">
          <motion.div
            initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.35 }}
            transition={{ duration: 0.6, ease }}
            className="mb-12 max-w-3xl"
          >
            <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#0ea5e9]">Workflow</p>
            <h2 className="mt-3 font-['Sora'] text-4xl font-extrabold tracking-tight text-[#020617] sm:text-5xl">
              One upload. Four precise steps. Ready-to-post reels.
            </h2>
            <p className="mt-4 text-lg font-medium text-[#475569]">
              Designed for busy agents and media teams who need consistent output without timeline editing.
            </p>
          </motion.div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {pipelineSteps.map((item, index) => (
              <motion.article
                key={item.step}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 26 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.55, ease, delay: prefersReducedMotion ? 0 : index * 0.08 }}
                className="group rounded-[1.7rem] border border-[#dbe3f1] bg-white/85 p-6 shadow-[0_20px_48px_rgba(15,23,42,0.06)] backdrop-blur"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#bfdbfe] bg-[#eff6ff] text-[#0284c7]">
                    <item.icon size={20} />
                  </div>
                  <span className="font-['Sora'] text-xs font-extrabold tracking-[0.18em] text-[#94a3b8]">{item.step}</span>
                </div>
                <h3 className="mt-5 font-['Sora'] text-xl font-bold tracking-tight text-[#0f172a]">{item.title}</h3>
                <p className="mt-3 text-sm font-semibold leading-relaxed text-[#64748b]">{item.desc}</p>
              </motion.article>
            ))}
          </div>
        </section>

        <section id="tutorial" className="mx-auto w-full max-w-7xl px-6 pb-20 pt-2 lg:px-10">
          <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={{ duration: 0.6, ease }}
            >
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#0ea5e9]">Tutorial</p>
              <h2 className="mt-3 font-['Sora'] text-4xl font-extrabold tracking-tight text-[#020617] sm:text-5xl">
                See Tutorials
              </h2>
              <p className="mt-4 text-lg font-medium leading-relaxed text-[#475569]">
                This walkthrough shows the exact user journey: upload one long tour, AI scene extraction, storyboard optimization, and final reel export.
              </p>
              <div className="mt-6 space-y-3">
                {[
                  'Supports one full home-tour video input',
                  'Applies scene diversity and opening/closing quality rules',
                  'Exports social-ready vertical format automatically',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-xl border border-[#e2e8f0] bg-white/85 px-4 py-3">
                    <CheckCircle2 size={16} className="mt-0.5 text-[#0ea5e9]" />
                    <p className="text-sm font-semibold text-[#334155]">{item}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={{ duration: 0.6, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
              className="rounded-[1.8rem] border border-[#dbe3f1] bg-white/85 p-4 shadow-[0_28px_60px_rgba(15,23,42,0.08)] backdrop-blur"
            >
              <video
                poster={heroPoster}
                controls
                playsInline
                preload="metadata"
                className="aspect-video w-full rounded-[1.2rem] border border-[#d6deeb] bg-[#020617] object-contain"
              >
                <source src="/tutorials/how-it-works.mp4" type="video/mp4" />
                <source src="/tutorials/how-it-work.mp4" type="video/mp4" />
                <source src="/demo/how-it-works.mp4" type="video/mp4" />
              </video>
            </motion.div>
          </div>
        </section>

        <section id="results" className="mx-auto w-full max-w-7xl px-6 pb-20 pt-8 lg:px-10">
          <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={{ duration: 0.6, ease }}
              className="rounded-[2rem] border border-[#dbe3f1] bg-white/85 p-8 shadow-[0_28px_60px_rgba(15,23,42,0.08)] backdrop-blur"
            >
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#0ea5e9]">Before</p>
              <h3 className="mt-3 font-['Sora'] text-2xl font-extrabold tracking-tight text-[#020617]">Raw Footage Problems</h3>
              <div className="mt-5 space-y-3">
                {[
                  'Long unedited walkthroughs with dead time',
                  'Shaky openings and inconsistent pacing',
                  'Repetitive room angles reducing retention',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] px-4 py-3">
                    <span className="mt-1 h-2 w-2 rounded-full bg-[#f97316]" />
                    <p className="text-sm font-semibold text-[#475569]">{item}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, x: 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={{ duration: 0.6, ease, delay: prefersReducedMotion ? 0 : 0.08 }}
              className="rounded-[2rem] border border-[#bbf7d0] bg-white/90 p-8 shadow-[0_28px_60px_rgba(16,185,129,0.12)] backdrop-blur"
            >
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#16a34a]">After</p>
              <h3 className="mt-3 font-['Sora'] text-2xl font-extrabold tracking-tight text-[#020617]">ReelForge Output</h3>
              <div className="mt-5 space-y-3">
                {[
                  'AI-selected highlight windows from full tour footage',
                  'Story-aware sequencing with room flow guardrails',
                  'Export-ready reels with style variations and audit metadata',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3 rounded-xl border border-[#d1fae5] bg-[#f0fdf4] px-4 py-3">
                    <CheckCircle2 size={16} className="mt-0.5 text-[#16a34a]" />
                    <p className="text-sm font-semibold text-[#166534]">{item}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        <section id="pricing" className="mx-auto w-full max-w-7xl px-6 pb-24 pt-2 lg:px-10">
          <div className="grid gap-6 rounded-[2rem] border border-[#dbe3f1] bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#0f766e] p-8 text-white shadow-[0_30px_70px_rgba(15,23,42,0.35)] lg:grid-cols-[1.2fr_0.8fr] lg:items-center lg:p-10">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#93c5fd]">Launch Faster</p>
              <h2 className="mt-3 font-['Sora'] text-3xl font-extrabold tracking-tight sm:text-4xl">
                Replace manual editing with one reliable AI reel pipeline.
              </h2>
              <div className="mt-6 space-y-3">
                {trustPoints.map((item) => (
                  <div key={item.text} className="flex items-start gap-3">
                    <item.icon size={17} className="mt-1 text-[#67e8f9]" />
                    <p className="text-sm font-semibold text-[#dbeafe]">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-white/20 bg-white/10 p-6 backdrop-blur">
              <p className="text-sm font-bold uppercase tracking-[0.1em] text-[#bae6fd]">Best For Teams</p>
              <p className="mt-2 font-['Sora'] text-4xl font-extrabold tracking-tight">$49<span className="text-base font-bold text-[#bfdbfe]">/mo</span></p>
              <p className="mt-2 text-sm font-semibold text-[#dbeafe]">Unlimited projects, analytics, and multi-variation rendering.</p>
              <div className="mt-5 flex flex-col gap-3">
                <Link
                  to="/signup"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-extrabold text-[#0f172a] transition hover:-translate-y-0.5"
                >
                  Start Free Trial
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center rounded-xl border border-white/35 px-5 py-3 text-sm font-extrabold text-white transition hover:bg-white/10"
                >
                  Sign In
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto w-full max-w-7xl px-6 pb-16 lg:px-10">
          <div className="grid gap-5 md:grid-cols-2">
            {testimonials.map((item, index) => (
              <motion.article
                key={item.name}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.35 }}
                transition={{ duration: 0.5, ease, delay: prefersReducedMotion ? 0 : index * 0.08 }}
                className="rounded-[1.5rem] border border-[#dbe3f1] bg-white/85 p-6 shadow-[0_20px_45px_rgba(15,23,42,0.06)] backdrop-blur"
              >
                <p className="text-base font-semibold leading-relaxed text-[#334155]">"{item.quote}"</p>
                <p className="mt-4 font-['Sora'] text-sm font-extrabold tracking-tight text-[#0f172a]">{item.name}</p>
                <p className="text-xs font-bold uppercase tracking-[0.1em] text-[#64748b]">{item.role}</p>
              </motion.article>
            ))}
          </div>
        </section>
      </main>

      <div className="fixed inset-x-4 bottom-4 z-30 sm:hidden">
        <div className="rounded-2xl border border-[#cbd5e1] bg-white/95 p-3 shadow-[0_18px_42px_rgba(15,23,42,0.22)] backdrop-blur">
          <div className="flex items-center gap-2">
            <Link
              to="/signup"
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-[#0f172a] px-4 py-3 text-sm font-extrabold text-white"
            >
              Start Free
              <ArrowRight size={15} />
            </Link>
            <a
              href="#tutorial"
              className="inline-flex items-center justify-center rounded-xl border border-[#cbd5e1] px-4 py-3 text-xs font-extrabold uppercase tracking-[0.08em] text-[#0f172a]"
            >
              Tutorial
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
