'use client'

import { useState, useEffect } from 'react'
import { questions, CATEGORY_LABELS, type QuestionCategory } from '@/data/questions'
import { ChevronDown, ChevronUp, CheckCircle2, Clock, Circle, Eye, EyeOff } from 'lucide-react'
import { AnnotatedParagraph } from '@/components/AnnotatedText'

type QStatus = 'not-started' | 'needs-work' | 'ready'

const STATUS_CONFIG: Record<QStatus, { label: string; icon: React.ReactNode; className: string }> = {
  'not-started': {
    label: 'Not started',
    icon: <Circle size={14} />,
    className: 'text-gray-500 border-gray-700',
  },
  'needs-work': {
    label: 'Needs work',
    icon: <Clock size={14} />,
    className: 'text-yellow-400 border-yellow-700 bg-yellow-900/20',
  },
  ready: {
    label: 'Ready',
    icon: <CheckCircle2 size={14} />,
    className: 'text-emerald-400 border-emerald-700 bg-emerald-900/20',
  },
}

const CATEGORIES: (QuestionCategory | 'all')[] = ['all', 'conceptual', 'system-design', 'practical']

// Markdown-lite renderer with glossary annotation support
function renderAnswer(text: string) {
  const lines = text.split('\n')
  return lines.map((line, i) => {
    if (line.startsWith('## ')) {
      return (
        <h3 key={i} className="font-semibold text-gray-200 mt-4 mb-1 text-sm">
          {line.slice(3)}
        </h3>
      )
    }
    if (line.startsWith('- ') || line.startsWith('* ')) {
      return (
        <li key={i} className="text-sm text-gray-300 ml-4 leading-relaxed list-disc">
          <AnnotatedParagraph text={line.slice(2)} />
        </li>
      )
    }
    if (/^\d+\. /.test(line)) {
      return (
        <li key={i} className="text-sm text-gray-300 ml-4 leading-relaxed list-decimal">
          <AnnotatedParagraph text={line.replace(/^\d+\. /, '')} />
        </li>
      )
    }
    if (line.startsWith('```') || line.endsWith('```')) return null
    if (line.trim() === '') return <div key={i} className="h-2" />
    return (
      <p key={i} className="text-sm text-gray-300 leading-relaxed">
        <AnnotatedParagraph text={line} />
      </p>
    )
  })
}

export default function QuestionsPage() {
  const [categoryFilter, setCategoryFilter] = useState<QuestionCategory | 'all'>('all')
  const [statuses, setStatuses] = useState<Record<string, QStatus>>({})
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [practiceMode, setPracticeMode] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('question-statuses')
    if (stored) setStatuses(JSON.parse(stored))
  }, [])

  const setStatus = (id: string, status: QStatus) => {
    const next = { ...statuses, [id]: status }
    setStatuses(next)
    localStorage.setItem('question-statuses', JSON.stringify(next))
  }

  const toggleExpanded = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const filteredQuestions = categoryFilter === 'all'
    ? questions
    : questions.filter((q) => q.category === categoryFilter)

  const readyCount = questions.filter((q) => statuses[q.id] === 'ready').length

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Interview Q&A</h1>
          <p className="text-sm text-gray-500 mt-1">
            {readyCount}/{questions.length} ready · Click any question to reveal the answer
          </p>
        </div>
        <button
          onClick={() => setPracticeMode((p) => !p)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm border transition-colors ${
            practiceMode
              ? 'bg-violet-600/20 text-violet-300 border-violet-600'
              : 'bg-gray-800 text-gray-400 border-gray-700 hover:border-gray-500'
          }`}
        >
          {practiceMode ? <EyeOff size={14} /> : <Eye size={14} />}
          Practice Mode
        </button>
      </div>

      {practiceMode && (
        <div className="mb-6 bg-violet-900/20 border border-violet-800/50 rounded-xl px-4 py-3 text-sm text-violet-300">
          Practice mode: answers are hidden. Click each question to reveal — try to answer in your head first.
        </div>
      )}

      {/* Progress bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="h-2 rounded-full bg-emerald-500 transition-all"
            style={{ width: `${(readyCount / questions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 mb-8 overflow-x-auto pb-1">
        {CATEGORIES.map((cat) => {
          const count = cat === 'all' ? questions.length : questions.filter((q) => q.category === cat).length
          return (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`shrink-0 px-4 py-2 rounded-xl text-sm border transition-colors ${
                categoryFilter === cat
                  ? 'bg-violet-600/20 text-violet-300 border-violet-600'
                  : 'text-gray-400 border-gray-700 hover:border-gray-500'
              }`}
            >
              {cat === 'all' ? 'All' : CATEGORY_LABELS[cat]} ({count})
            </button>
          )
        })}
      </div>

      {/* Questions */}
      <div className="space-y-3">
        {filteredQuestions.map((q) => {
          const isOpen = expanded.has(q.id) && !practiceMode || (expanded.has(q.id))
          const status = statuses[q.id] ?? 'not-started'
          const statusCfg = STATUS_CONFIG[status]

          return (
            <div
              key={q.id}
              className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
            >
              {/* Question header */}
              <button
                onClick={() => toggleExpanded(q.id)}
                className="w-full flex items-start gap-3 px-5 py-4 hover:bg-gray-800/50 transition-colors text-left"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full border border-gray-700">
                      {CATEGORY_LABELS[q.category]}
                    </span>
                    {q.tags.slice(0, 2).map((tag) => (
                      <span key={tag} className="text-xs text-gray-600">#{tag}</span>
                    ))}
                  </div>
                  <p className="font-medium text-gray-200 text-sm leading-relaxed">
                    "{q.question}"
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0 pt-0.5">
                  {isOpen ? (
                    <ChevronUp size={16} className="text-gray-500" />
                  ) : (
                    <ChevronDown size={16} className="text-gray-500" />
                  )}
                </div>
              </button>

              {/* Answer */}
              {isOpen && (
                <div className="border-t border-gray-800 px-5 py-4">
                  <div className="space-y-1.5 mb-5">
                    {renderAnswer(q.answer)}
                  </div>

                  {/* Status buttons */}
                  <div className="flex items-center gap-2 pt-3 border-t border-gray-800">
                    <span className="text-xs text-gray-500 mr-1">Mark as:</span>
                    {(['not-started', 'needs-work', 'ready'] as QStatus[]).map((s) => {
                      const cfg = STATUS_CONFIG[s]
                      return (
                        <button
                          key={s}
                          onClick={() => setStatus(q.id, s)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border transition-colors ${
                            status === s ? cfg.className : 'text-gray-500 border-gray-700 hover:border-gray-500'
                          }`}
                        >
                          {cfg.icon} {cfg.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
