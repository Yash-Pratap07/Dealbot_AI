'use client'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowsRightLeftIcon,
  ChartBarSquareIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ScaleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import type { ComponentType, SVGProps } from 'react'

type IconType = ComponentType<SVGProps<SVGSVGElement>>

const features = [
  {
    title: 'Market Discovery Engine',
    description: 'Aggregate listings and normalize landed cost, shipping SLA, and seller reliability in one view.',
    icon: ChartBarSquareIcon,
  },
  {
    title: 'Negotiation Co-Pilot',
    description: 'Recommend counter windows using margin target, seller behavior, and response latency signals.',
    icon: ArrowsRightLeftIcon,
  },
  {
    title: 'Verified Closure',
    description: 'Convert accepted terms into contracts and settlement-ready records with clear audit history.',
    icon: ShieldCheckIcon,
  },
]

const metrics = [
  { value: '12%', label: 'avg negotiated savings' },
  { value: '2.3x', label: 'faster closure cycle' },
  { value: '98%', label: 'session completion' },
]

const steps = [
  {
    title: 'Capture Intent',
    description: 'Capture product target, budget band, delivery SLA, and fallback constraints.',
  },
  {
    title: 'Run Live Rounds',
    description: 'Execute structured rounds with explainable counter strategy and confidence scores.',
  },
  {
    title: 'Finalize Terms',
    description: 'Finalize terms, lock contract fields, and hand off to settlement workflow.',
  },
]

const workflow = [
  { label: 'Input', value: 'Intent + constraints', icon: SparklesIcon },
  { label: 'Engine', value: 'Discovery + trust + ranking', icon: CpuChipIcon },
  { label: 'Negotiation', value: 'Live buyer/seller rounds', icon: ArrowsRightLeftIcon },
  { label: 'Closure', value: 'Contract + settlement', icon: ScaleIcon },
]

const useCases = [
  {
    title: 'Procurement Teams',
    description: 'Shorten hardware and software buying cycles while preserving approval controls.',
  },
  {
    title: 'Marketplace Operations',
    description: 'Automate first-pass negotiation and route exceptions for human decision.',
  },
  {
    title: 'High-Value Buyers',
    description: 'Compare trusted sellers and negotiate expensive purchases with clear risk signals.',
  },
]

const modules = [
  {
    title: 'Search and Ranking',
    route: '/dashboard/search-product',
    detail: 'Compare offers across sellers with normalized pricing and rank context.',
  },
  {
    title: 'Trust Analysis',
    route: '/dashboard/ai-results',
    detail: 'Score seller reliability using reviews, response behavior, and verification signals.',
  },
  {
    title: 'Negotiation Room',
    route: '/dashboard/negotiation-room',
    detail: 'Run live offer rounds with guided counters and decision visibility.',
  },
]

const liveLog = [
  { time: '00:03', text: 'Buyer opens at $1,520', tone: 'text-slate-700' },
  { time: '00:11', text: 'Seller counters at $1,610', tone: 'text-slate-700' },
  { time: '00:19', text: 'DealBot suggests $1,565 + escrow clause', tone: 'text-sky-700' },
  { time: '00:28', text: 'Seller accepts with 48h dispatch', tone: 'text-emerald-700' },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-[#fffaf2] text-[#1f2937]">
      <header className="sticky top-0 z-40 border-b border-[#e6dfd1] bg-[#fffaf2]/95 backdrop-blur-sm">
        <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <a href="#hero" className="font-display text-lg tracking-tight">DealBot AI</a>
          <div className="hidden items-center gap-6 text-sm text-slate-600 md:flex">
            <a href="#features" className="transition hover:text-[#0ea5e9]">Features</a>
            <a href="#workflow" className="transition hover:text-[#0ea5e9]">Workflow</a>
            <a href="#use-cases" className="transition hover:text-[#0ea5e9]">Use Cases</a>
            <a href="#demo" className="transition hover:text-[#0ea5e9]">Demo</a>
          </div>
          <Link href="/register" className="rounded-lg bg-[#38BDF8] px-4 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-sky-500">
            Start Live Demo
          </Link>
        </nav>
      </header>

      <section id="hero" className="mx-auto grid w-full max-w-6xl grid-cols-1 gap-8 px-6 pb-14 pt-12 md:grid-cols-12 md:pt-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="space-y-7 md:col-span-7"
        >
          <span className="inline-flex rounded-full border border-[#d9cfbc] bg-[#f7f0e3] px-3 py-1 text-xs tracking-[0.16em] text-[#7a6f5c]">
            LIVE NEGOTIATION ENGINE
          </span>

          <h1 className="font-display max-w-3xl text-4xl leading-tight sm:text-5xl lg:text-6xl">
            Negotiate better deals in real time.
          </h1>

          <p className="max-w-2xl text-base text-slate-600 sm:text-lg">
            DealBot AI discovers products, scores seller trust, runs live negotiation rounds, and finalizes contract-ready outcomes.
          </p>

          <div className="flex flex-wrap gap-3">
            <Link href="/register" className="rounded-lg bg-[#38BDF8] px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-sky-500">
              Start Live Demo
            </Link>
            <Link href="/login" className="rounded-lg border border-[#d7d0c3] bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-[#38BDF8] hover:text-[#0284c7]">
              Open Dashboard
            </Link>
          </div>

          <div className="grid gap-3 pt-2 sm:grid-cols-3">
            {metrics.map((item, idx) => (
              <motion.div
                key={item.label}
                whileHover={{ y: -3 }}
                transition={{ duration: 0.2 }}
                className={`rounded-lg border border-[#e1d8c9] bg-[#fffdf8] p-4 shadow-sm ${idx === 1 ? 'sm:translate-y-3' : ''}`}
              >
                <p className="font-display text-2xl">{item.value}</p>
                <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.08 }}
          className="relative md:col-span-5 md:mt-8"
        >
          <div className="rounded-xl border border-[#e1d8c9] bg-white p-5 shadow-[0_16px_34px_rgba(148,130,104,0.16)]">
            <div className="mb-4 flex items-center justify-between border-b border-[#ece4d8] pb-3">
              <p className="font-display text-sm tracking-wide text-slate-700">Live Deal Room</p>
              <span className="rounded-full bg-[#eef7ff] px-2 py-1 text-[11px] text-sky-700">sync active</span>
            </div>
            <div className="space-y-2">
              {liveLog.map((item, i) => (
                <motion.div
                  key={item.text}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.18 + i * 0.09 }}
                  className="rounded-md border border-[#ece4d8] bg-[#fffdf8] px-3 py-2"
                >
                  <p className="text-[11px] text-slate-500">{item.time}</p>
                  <p className={`mt-1 text-sm ${item.tone}`}>{item.text}</p>
                </motion.div>
              ))}
            </div>
          </div>

          <motion.div
            whileHover={{ y: -3 }}
            transition={{ duration: 0.2 }}
            className="-mt-5 ml-8 w-[88%] rounded-lg border border-[#e1d8c9] bg-[#fff6ea] p-4"
          >
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">AI reasoning</p>
            <p className="mt-2 text-sm text-slate-700">
              Counter at $1,565 improves acceptance probability by 18% while maintaining delivery reliability.
            </p>
          </motion.div>
        </motion.div>
      </section>

      <section id="features" className="mx-auto w-full max-w-6xl px-6 pb-14">
        <h2 className="font-display text-3xl">Built for real negotiation workflows</h2>
        <p className="mt-2 max-w-2xl text-slate-600">
          Product modules are designed for practical buying decisions, not generic chatbot outputs.
        </p>
        <div className="mt-7 grid gap-4 md:grid-cols-3">
          {features.map((feature, i) => {
            const Icon = feature.icon as IconType
            return (
              <motion.article
                key={feature.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.35 }}
                transition={{ duration: 0.45, delay: i * 0.06 }}
                whileHover={{ y: -3 }}
                className={`rounded-xl border border-[#e1d8c9] bg-white p-5 shadow-sm transition ${i === 1 ? 'md:mt-4' : ''}`}
              >
                <div className="inline-flex rounded-md border border-[#d7d0c3] bg-[#fff8ee] p-2">
                  <Icon className="h-5 w-5 text-[#0ea5e9]" />
                </div>
                <h3 className="mt-4 font-display text-xl">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
              </motion.article>
            )
          })}
        </div>
      </section>

      <section id="workflow" className="mx-auto w-full max-w-6xl px-6 pb-14">
        <div className="rounded-xl border border-[#e1d8c9] bg-[#fffdf8] p-6 md:p-7">
          <h2 className="font-display text-3xl">Product architecture</h2>
          <p className="mt-2 max-w-2xl text-slate-600">One pipeline from buyer intent to settlement, with visible checkpoints at each stage.</p>

          <div className="mt-7 grid gap-3 md:grid-cols-4">
            {workflow.map((item, i) => {
              const Icon = item.icon as IconType
              return (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ delay: i * 0.08 }}
                  className="relative rounded-lg border border-[#e8dfd2] bg-white p-4"
                >
                  <Icon className="h-5 w-5 text-[#0ea5e9]" />
                  <p className="mt-3 text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
                  <p className="mt-1 text-sm text-slate-700">{item.value}</p>
                  {i < workflow.length - 1 && (
                    <span className="absolute -right-2 top-1/2 hidden h-px w-3 bg-[#d5cab8] md:block" />
                  )}
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 pb-14">
        <div className="grid gap-5 md:grid-cols-12">
          <div className="rounded-xl border border-[#e1d8c9] bg-white p-6 md:col-span-7">
            <h2 className="font-display text-3xl">How it works</h2>
            <div className="mt-6 space-y-4">
              {steps.map((step, i) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ delay: i * 0.08 }}
                  className={`rounded-lg border border-[#e8dfd2] bg-[#fffdf8] p-4 ${i === 1 ? 'ml-2' : ''}`}
                >
                  <p className="text-xs uppercase tracking-wide text-[#0284c7]">Step {i + 1}</p>
                  <h3 className="mt-2 font-display text-xl">{step.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{step.description}</p>
                </motion.div>
              ))}
            </div>
          </div>

          <div id="demo" className="rounded-xl border border-[#e1d8c9] bg-[#fffdf8] p-6 md:col-span-5 md:mt-8">
            <h2 className="font-display text-3xl">Live product modules</h2>
            <p className="mt-2 text-sm text-slate-600">Jump to real surfaces from the running product.</p>
            <div className="mt-5 space-y-3">
              {modules.map((module, i) => (
                <motion.div
                  key={module.title}
                  initial={{ opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ delay: i * 0.07 }}
                  whileHover={{ y: -2 }}
                  className={`rounded-lg border border-[#e8dfd2] bg-white p-4 ${i === 1 ? 'ml-4' : ''}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-display text-lg">{module.title}</h3>
                    <Link
                      href={module.route}
                      className="rounded-md border border-[#d7d0c3] px-3 py-1 text-xs font-semibold text-slate-700 transition hover:border-[#38BDF8] hover:text-[#0284c7]"
                    >
                      Open
                    </Link>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{module.detail}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="use-cases" className="mx-auto w-full max-w-6xl px-6 pb-16">
        <h2 className="font-display text-3xl">Use cases</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {useCases.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.35 }}
              transition={{ delay: i * 0.06 }}
              whileHover={{ y: -2 }}
              className="rounded-xl border border-[#e1d8c9] bg-white p-5 shadow-sm"
            >
              <h3 className="font-display text-xl">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.description}</p>
            </motion.div>
          ))}
        </div>

        <div className="mt-8 rounded-xl border border-[#e1d8c9] bg-[#fff8ee] p-6 text-center">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Ready to launch</p>
          <h2 className="mt-2 font-display text-3xl">Run your first live deal in 2 minutes.</h2>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link href="/register" className="rounded-lg bg-[#38BDF8] px-6 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-sky-500">
              Create Account
            </Link>
            <Link href="/login" className="rounded-lg border border-[#d7d0c3] bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-[#38BDF8] hover:text-[#0284c7]">
              Sign In
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
