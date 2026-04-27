'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { CheckCircle2, Circle, Layers, MessageSquare, Cpu, BookOpen, Terminal, ArrowRight } from 'lucide-react'

type Week = {
  label: string
  color: string
  items: { id: string; label: string; file?: string; note?: string; slug?: string }[]
}

const WEEKS: Week[] = [
  {
    label: 'Week 1 — Foundations',
    color: 'text-blue-400 border-blue-800',
    items: [
      { id: 'w1-1', slug: 'prompting-strategies', label: 'Prompting strategies', file: '01_foundations/llm_basics/prompting_strategies.py' },
      { id: 'w1-2', slug: 'temperature-demo', label: 'Temperature demo', file: '01_foundations/llm_basics/temperature_demo.py' },
      { id: 'w1-3', slug: 'hallucination-demo', label: 'Hallucination demo', file: '01_foundations/llm_basics/hallucination_demo.py' },
      { id: 'w1-4', slug: 'cosine-similarity', label: 'Cosine similarity', file: '01_foundations/embeddings/cosine_similarity.py', note: 'No API needed' },
      { id: 'w1-5', slug: 'chunking-strategies', label: 'Chunking strategies', file: '01_foundations/embeddings/chunking_strategies.py', note: 'No API needed' },
      { id: 'w1-6', slug: 'vector-search-demo', label: 'Vector search demo', file: '01_foundations/embeddings/vector_search_demo.py', note: 'No API needed' },
      { id: 'w1-7', slug: 'rag-vs-finetuning', label: 'RAG vs fine-tuning', file: '01_foundations/ml_concepts/rag_vs_finetuning.py' },
      { id: 'w1-8', slug: 'evaluation-metrics', label: 'Evaluation metrics', file: '01_foundations/ml_concepts/evaluation_metrics.py', note: 'No API needed' },
    ],
  },
  {
    label: 'Week 2 — Agentic Core',
    color: 'text-violet-400 border-violet-800',
    items: [
      { id: 'w2-1', slug: 'tool-registry', label: 'Tool registry pattern', file: '02_agentic_core/tool_use/tool_registry.py', note: 'No API needed' },
      { id: 'w2-2', slug: 'sample-tools', label: 'Sample tools', file: '02_agentic_core/tool_use/sample_tools.py', note: 'No API needed' },
      { id: 'w2-3', slug: 'function-calling', label: 'Function calling', file: '02_agentic_core/tool_use/function_calling.py' },
      { id: 'w2-4', slug: 'short-term-memory', label: 'Short-term memory', file: '02_agentic_core/memory/short_term.py' },
      { id: 'w2-5', slug: 'long-term-memory', label: 'Long-term memory', file: '02_agentic_core/memory/long_term.py', note: 'No API needed' },
      { id: 'w2-6', slug: 'episodic-memory', label: 'Episodic memory', file: '02_agentic_core/memory/episodic.py', note: 'No API needed' },
      { id: 'w2-7', slug: 'semantic-memory', label: 'Semantic memory', file: '02_agentic_core/memory/semantic.py', note: 'No API needed' },
      { id: 'w2-8', slug: 'react-agent', label: 'ReAct agent ⭐', file: '02_agentic_core/patterns/react_agent.py', note: 'Most important' },
      { id: 'w2-9', slug: 'plan-and-execute', label: 'Plan-and-execute', file: '02_agentic_core/patterns/plan_and_execute.py' },
      { id: 'w2-10', slug: 'human-in-the-loop', label: 'Human-in-the-loop', file: '02_agentic_core/patterns/human_in_loop.py' },
    ],
  },
  {
    label: 'Week 3 — System Design',
    color: 'text-cyan-400 border-cyan-800',
    items: [
      { id: 'w3-1', slug: 'orchestrator-pattern', label: 'Orchestrator pattern', file: '03_system_design/orchestrator.py' },
      { id: 'w3-2', slug: 'llm-gateway', label: 'LLM gateway', file: '03_system_design/llm_gateway.py' },
      { id: 'w3-3', slug: 'tool-registry-advanced', label: 'Tool registry (advanced)', file: '03_system_design/tool_registry.py', note: 'No API needed' },
      { id: 'w3-4', slug: 'observability', label: 'Observability / tracing', file: '03_system_design/observability.py', note: 'No API needed' },
      { id: 'w3-5', slug: 'guardrails', label: 'Guardrails', file: '04_resiliency/guardrails.py', note: 'No API needed' },
      { id: 'w3-6', slug: 'retry-strategies', label: 'Retry strategies', file: '04_resiliency/retry_strategies.py' },
      { id: 'w3-7', slug: 'loop-control', label: 'Loop control', file: '04_resiliency/loop_control.py', note: 'No API needed' },
      { id: 'w3-8', slug: 'structured-outputs', label: 'Structured outputs', file: '04_resiliency/structured_outputs.py' },
    ],
  },
  {
    label: 'Week 4 — Projects',
    color: 'text-emerald-400 border-emerald-800',
    items: [
      { id: 'w4-1', slug: 'prompt-unit-tests', label: 'Eval: prompt unit tests', file: '04_resiliency/evaluation/prompt_unit_tests.py', note: 'Run with pytest' },
      { id: 'w4-2', slug: 'golden-dataset', label: 'Eval: golden dataset', file: '04_resiliency/evaluation/golden_dataset.py' },
      { id: 'w4-3', slug: 'project1-tool-agent', label: 'Project 1: Tool agent', file: '05_projects/project1_tool_agent/agent.py' },
      { id: 'w4-4', slug: 'project2-rag-ingest', label: 'Project 2: RAG ingest', file: '05_projects/project2_rag/ingest.py', note: 'Run first' },
      { id: 'w4-5', slug: 'project2-rag-query', label: 'Project 2: RAG query', file: '05_projects/project2_rag/rag_chain.py' },
      { id: 'w4-6', slug: 'project2-rag-api', label: 'Project 2: RAG API', file: '05_projects/project2_rag/api.py', note: 'uvicorn' },
      { id: 'w4-7', slug: 'project3-multi-agent', label: 'Project 3: Multi-agent', file: '05_projects/project3_multi_agent/workflow.py' },
    ],
  },
  {
    label: 'Interview Review',
    color: 'text-orange-400 border-orange-800',
    items: [
      { id: 'ir-1', slug: '/flashcards', label: 'All 32 flashcards', note: 'Flashcards page' },
      { id: 'ir-2', slug: '/system-design', label: '3 system design templates', note: 'System Design page' },
      { id: 'ir-3', slug: '/questions', label: '15 common questions', note: 'Q&A page' },
    ],
  },
]

const QUICK_LINKS = [
  { href: '/flashcards', label: 'Flashcards', icon: Layers, desc: '32 key terms', color: 'text-blue-400' },
  { href: '/questions', label: 'Q&A Practice', icon: MessageSquare, desc: '15 interview questions', color: 'text-violet-400' },
  { href: '/system-design', label: 'System Design', icon: Cpu, desc: '3 architecture templates', color: 'text-cyan-400' },
  { href: '/reference', label: 'Reference', icon: BookOpen, desc: 'Searchable term index', color: 'text-emerald-400' },
]

export default function HomePage() {
  const [completed, setCompleted] = useState<Set<string>>(new Set())

  useEffect(() => {
    const stored = localStorage.getItem('learning-path-completed')
    if (stored) setCompleted(new Set(JSON.parse(stored)))
  }, [])

  const toggle = (id: string) => {
    const next = new Set(completed)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setCompleted(next)
    localStorage.setItem('learning-path-completed', JSON.stringify([...next]))
  }

  const totalItems = WEEKS.flatMap((w) => w.items).length
  const completedCount = WEEKS.flatMap((w) => w.items).filter((item) =>
    completed.has(item.id)
  ).length
  const progressPct = Math.round((completedCount / totalItems) * 100)

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-100 mb-2">Agentic AI Interview Prep</h1>
        <p className="text-gray-400">
          Work through each section in order. Run the scripts, study the patterns, then
          review before your interview.
        </p>
      </div>

      {/* Progress bar */}
      <div className="mb-10 bg-gray-900 rounded-xl p-5 border border-gray-800">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-medium text-gray-300">Overall Progress</span>
          <span className="text-sm text-gray-400">
            {completedCount}/{totalItems} items
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-violet-600 to-blue-500 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="text-right text-xs text-gray-500 mt-1">{progressPct}%</div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 gap-3 mb-10">
        {QUICK_LINKS.map(({ href, label, icon: Icon, desc, color }) => (
          <Link
            key={href}
            href={href}
            className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-600 transition-colors group"
          >
            <Icon size={20} className={`${color} mb-2`} />
            <div className="font-medium text-sm text-gray-200 group-hover:text-white">{label}</div>
            <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
          </Link>
        ))}
      </div>

      {/* Learning path weeks */}
      <div className="space-y-6">
        {WEEKS.map((week) => {
          const weekCompleted = week.items.filter((i) => completed.has(i.id)).length
          return (
            <div key={week.label} className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
              <div className={`flex items-center justify-between px-5 py-3 border-b border-gray-800`}>
                <h2 className={`font-semibold text-sm ${week.color.split(' ')[0]}`}>
                  {week.label}
                </h2>
                <span className="text-xs text-gray-500">
                  {weekCompleted}/{week.items.length}
                </span>
              </div>
              <div className="divide-y divide-gray-800/50">
                {week.items.map((item) => {
                  const done = completed.has(item.id)
                  // Interview review slugs are absolute paths (/flashcards etc.)
                  // Lesson slugs are relative (prompting-strategies etc.)
                  const href = item.slug
                    ? item.slug.startsWith('/')
                      ? item.slug
                      : `/learn/${item.slug}`
                    : null

                  return (
                    <div
                      key={item.id}
                      className="flex items-stretch divide-x divide-gray-800/50"
                    >
                      {/* Checkbox — toggles completion only */}
                      <button
                        onClick={() => toggle(item.id)}
                        className="flex items-center justify-center px-4 py-3 hover:bg-gray-800/60 transition-colors shrink-0"
                        title={done ? 'Mark incomplete' : 'Mark complete'}
                      >
                        {done ? (
                          <CheckCircle2 size={16} className="text-emerald-400" />
                        ) : (
                          <Circle size={16} className="text-gray-600" />
                        )}
                      </button>

                      {/* Label — links to lesson if available, otherwise plain */}
                      {href ? (
                        <Link
                          href={href}
                          className="flex-1 flex items-center justify-between gap-3 px-4 py-3 hover:bg-gray-800/50 transition-colors group min-w-0"
                        >
                          <div className="min-w-0">
                            <span className={`text-sm ${done ? 'text-gray-500 line-through' : 'text-gray-200 group-hover:text-white'}`}>
                              {item.label}
                            </span>
                            {item.file && (
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <Terminal size={10} className="text-gray-600" />
                                <code className="text-[11px] text-gray-500 font-mono truncate">
                                  {item.file}
                                </code>
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            {item.note && (
                              <span className="text-[11px] text-gray-600">{item.note}</span>
                            )}
                            <ArrowRight size={13} className="text-gray-600 group-hover:text-violet-400 transition-colors" />
                          </div>
                        </Link>
                      ) : (
                        <div className="flex-1 flex items-center justify-between gap-3 px-4 py-3 min-w-0">
                          <span className={`text-sm ${done ? 'text-gray-500 line-through' : 'text-gray-400'}`}>
                            {item.label}
                          </span>
                          {item.note && (
                            <span className="text-[11px] text-gray-600 shrink-0">{item.note}</span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-8 text-center text-xs text-gray-600">
        Progress saved automatically in browser storage
      </div>
    </div>
  )
}
