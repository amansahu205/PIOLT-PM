'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const features = [
  {
    tag: 'Always On',
    headline: 'Watches every\ntool you use.',
    body: 'PilotPM connects to GitHub, Linear, Slack, Jira, and more. It reads commit diffs, issue updates, and thread context — so you never have to ask "what changed?"',
    visual: <VisualActivity />,
    reverse: false,
  },
  {
    tag: 'Zero Meetings',
    headline: 'Standups are\nso last decade.',
    body: 'Every morning your team gets a concise AI-generated summary of exactly what happened, what\'s blocked, and what\'s next. No sync call needed.',
    visual: <VisualSummary />,
    reverse: true,
  },
  {
    tag: 'Smart Context',
    headline: 'One question.\nEverything answers.',
    body: 'Ask PilotPM anything in plain English. "Why is auth broken?" It cross-references commits, Slack threads, and tickets in seconds.',
    visual: <VisualSearch />,
    reverse: false,
  },
  {
    tag: 'Risk Detection',
    headline: 'Flags blockers\nbefore they block.',
    body: 'PilotPM detects velocity drops, unreviewed PRs, and scope creep in real time — surfacing risks before they become incidents.',
    visual: <VisualRisk />,
    reverse: true,
  },
  {
    tag: 'Ship Faster',
    headline: 'Your PM.\nOn autopilot.',
    body: 'From sprint planning to retrospectives, PilotPM generates drafts, updates roadmaps, and closes the loop — so engineers ship and PMs lead.',
    visual: <VisualAutopilot />,
    reverse: false,
  },
]

function VisualActivity() {
  const items = [
    { label: 'auth-fix merged', time: '2m ago', color: '#22d3ee' },
    { label: 'new issue opened', time: '5m ago', color: '#94a3b8' },
    { label: 'PR review requested', time: '9m ago', color: '#22d3ee' },
    { label: 'deploy succeeded', time: '12m ago', color: '#34d399' },
    { label: 'test suite passed', time: '15m ago', color: '#34d399' },
  ]
  return (
    <div className="w-full rounded-2xl border border-[#1e2d45] bg-[#0d1424] p-6 space-y-3">
      {items.map((item, i) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, x: -16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.1 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-sm text-white/80">{item.label}</span>
          </div>
          <span className="text-xs text-white/30">{item.time}</span>
        </motion.div>
      ))}
    </div>
  )
}

function VisualSummary() {
  return (
    <div className="w-full rounded-2xl border border-[#1e2d45] bg-[#0d1424] p-6">
      <div className="mb-4 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-cyan-400" />
        <span className="text-xs uppercase tracking-widest text-cyan-400/80" style={{ fontFamily: 'var(--font-syne)' }}>
          Daily Brief · Mon 7:00 AM
        </span>
      </div>
      <div className="space-y-3 text-sm text-white/70 leading-relaxed">
        <p>
          <span className="text-white font-medium">Shipped:</span> Auth refactor merged, 3 bugs closed, deploy green.
        </p>
        <p>
          <span className="text-white font-medium">Blocked:</span> Payment webhook waiting on Stripe review (48h).
        </p>
        <p>
          <span className="text-white font-medium">Today:</span> 2 PRs need review, sprint ends Friday, 4 tickets unestimated.
        </p>
      </div>
      <div
        className="mt-5 h-px w-full"
        style={{ background: 'linear-gradient(to right, rgba(34,211,238,0.3), transparent)' }}
      />
      <p className="mt-3 text-xs text-white/30">No standup scheduled · PilotPM</p>
    </div>
  )
}

function VisualSearch() {
  return (
    <div className="w-full rounded-2xl border border-[#1e2d45] bg-[#0d1424] p-6 space-y-4">
      <div className="flex items-center gap-3 rounded-xl border border-[#1e2d45] bg-[#020817] px-4 py-3">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <span className="text-sm text-white/40">Why is auth broken?</span>
      </div>
      <div className="space-y-2 text-sm text-white/70 leading-relaxed">
        <p className="text-cyan-400 font-medium">PilotPM found 3 related sources:</p>
        <div className="flex gap-2 flex-wrap">
          {['PR #204', 'Slack #backend', 'Issue #89'].map((s) => (
            <span key={s} className="rounded-full border border-[#1e2d45] px-3 py-1 text-xs text-white/60">
              {s}
            </span>
          ))}
        </div>
        <p className="pt-1 text-white/60">
          The session token expiry was shortened in PR #204 without updating the refresh logic. Issue #89 was filed 6h
          ago by @kim.
        </p>
      </div>
    </div>
  )
}

function VisualRisk() {
  const risks = [
    { label: 'Velocity drop detected', level: 'high', icon: '↘' },
    { label: '5 PRs unreviewed > 48h', level: 'medium', icon: '⏳' },
    { label: 'Sprint capacity at 112%', level: 'high', icon: '⚠' },
  ]
  const colors: Record<string, string> = { high: '#f87171', medium: '#fbbf24' }
  return (
    <div className="w-full rounded-2xl border border-[#1e2d45] bg-[#0d1424] p-6 space-y-3">
      {risks.map((r, i) => (
        <motion.div
          key={r.label}
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.12 }}
          className="flex items-center gap-3 rounded-xl border px-4 py-3"
          style={{ borderColor: `${colors[r.level]}30`, backgroundColor: `${colors[r.level]}08` }}
        >
          <span style={{ color: colors[r.level] }} className="text-lg leading-none">
            {r.icon}
          </span>
          <span className="text-sm text-white/80">{r.label}</span>
          <span
            className="ml-auto rounded-full px-2 py-0.5 text-xs font-medium uppercase tracking-wide"
            style={{ color: colors[r.level], backgroundColor: `${colors[r.level]}15` }}
          >
            {r.level}
          </span>
        </motion.div>
      ))}
    </div>
  )
}

function VisualAutopilot() {
  const steps = ['Sprint plan drafted', 'Roadmap updated', 'Retro summary sent', 'Tickets closed']
  return (
    <div className="w-full rounded-2xl border border-[#1e2d45] bg-[#0d1424] p-6">
      <div className="flex items-center justify-between mb-5">
        <span className="text-xs uppercase tracking-widest text-cyan-400/80" style={{ fontFamily: 'var(--font-syne)' }}>
          PilotPM Autopilot
        </span>
        <span className="flex items-center gap-1.5 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
          Active
        </span>
      </div>
      <div className="relative pl-6">
        <div className="absolute left-[7px] top-0 bottom-0 w-px bg-[#1e2d45]" />
        {steps.map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            className="relative mb-4 flex items-center gap-3"
          >
            <span className="absolute -left-6 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-400/20 ring-1 ring-cyan-400/50">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            </span>
            <span className="text-sm text-white/70">{step}</span>
            <span className="ml-auto text-xs text-cyan-400/60">✓</span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function FeatureRow({
  tag,
  headline,
  body,
  visual,
  reverse,
}: {
  tag: string
  headline: string
  body: string
  visual: React.ReactNode
  reverse: boolean
}) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 60 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className={`flex flex-col gap-12 py-24 lg:flex-row lg:items-center lg:gap-20 ${
        reverse ? 'lg:flex-row-reverse' : ''
      }`}
    >
      {/* Text */}
      <div className="flex-1 space-y-5">
        <span
          className="inline-block rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium uppercase tracking-widest text-cyan-400"
          style={{ fontFamily: 'var(--font-syne)' }}
        >
          {tag}
        </span>
        <h2
          className="text-balance whitespace-pre-line text-4xl font-bold leading-tight text-white lg:text-5xl"
          style={{ fontFamily: 'var(--font-syne)' }}
        >
          {headline}
        </h2>
        <p className="text-lg leading-relaxed text-white/50">{body}</p>
      </div>

      {/* Visual */}
      <div className="flex-1">{visual}</div>
    </motion.div>
  )
}

export default function FeatureSections() {
  return (
    <section id="features" className="bg-[#020817]">
      <div className="mx-auto max-w-6xl px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="pb-8 pt-28 text-center"
        >
          <p
            className="mb-4 text-sm uppercase tracking-widest text-cyan-400/70"
            style={{ fontFamily: 'var(--font-syne)' }}
          >
            How it works
          </p>
          <h2
            className="text-balance text-4xl font-bold text-white lg:text-5xl"
            style={{ fontFamily: 'var(--font-syne)' }}
          >
            Your team, running on autopilot.
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-white/50">
            PilotPM sits quietly in the background — then surfaces exactly the right signal at exactly the right moment.
          </p>
        </motion.div>

        {/* Feature rows */}
        {features.map((f) => (
          <FeatureRow key={f.tag} {...f} />
        ))}

        {/* CTA section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="border-t border-[#1e2d45] py-28 text-center"
        >
          <h2
            className="mb-6 text-balance text-4xl font-bold text-white lg:text-5xl"
            style={{ fontFamily: 'var(--font-syne)' }}
          >
            Ready to ditch standups?
          </h2>
          <p className="mx-auto mb-10 max-w-lg text-lg text-white/50">
            Join engineering teams that ship faster, communicate better, and never ask "what&apos;s the status?" again.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <a
              href="#"
              className="rounded-full bg-cyan-400 px-8 py-4 text-base font-semibold text-[#020817] transition-all hover:bg-cyan-300"
              style={{
                fontFamily: 'var(--font-syne)',
                boxShadow: '0 0 32px 4px rgba(34,211,238,0.3)',
              }}
            >
              Start for free
            </a>
            <a
              href="#"
              className="rounded-full border border-[#1e2d45] px-8 py-4 text-base font-medium text-white/70 transition-all hover:border-white/30 hover:text-white"
              style={{ fontFamily: 'var(--font-syne)' }}
            >
              Watch a demo
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
