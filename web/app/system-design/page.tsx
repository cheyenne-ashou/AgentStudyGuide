'use client'

import { useState } from 'react'
import { systemDesigns, blankTemplate } from '@/data/system-designs'
import { CheckSquare, Square } from 'lucide-react'

const TABS = [
  ...systemDesigns.map((d) => ({ id: d.id, label: d.title })),
  { id: 'blank', label: 'Blank Template' },
]

export default function SystemDesignPage() {
  const [activeTab, setActiveTab] = useState(systemDesigns[0].id)
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set())

  const toggleCheck = (key: string) => {
    setCheckedItems((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const design = systemDesigns.find((d) => d.id === activeTab)

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">System Design</h1>
        <p className="text-sm text-gray-500 mt-1">
          3 architecture templates. Study each one until you can sketch it from memory.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-8 overflow-x-auto pb-1">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`shrink-0 px-4 py-2 rounded-xl text-sm border transition-colors ${
              activeTab === id
                ? 'bg-cyan-600/20 text-cyan-300 border-cyan-600'
                : 'text-gray-400 border-gray-700 hover:border-gray-500'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Blank template */}
      {activeTab === 'blank' ? (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="font-semibold text-gray-200 mb-4">Blank Design Template</h2>
            <p className="text-sm text-gray-400 mb-6">
              Use this checklist for any system design question. Check off each component as you cover it.
            </p>

            {[
              { title: 'Components', items: blankTemplate.components, prefix: 'comp' },
              { title: 'Data Flow', items: blankTemplate.dataFlow, prefix: 'flow' },
              { title: 'Scaling', items: blankTemplate.scaling, prefix: 'scale' },
              { title: 'Resiliency', items: blankTemplate.resiliency, prefix: 'res' },
            ].map(({ title, items, prefix }) => (
              <div key={prefix} className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">{title}</h3>
                <div className="space-y-2">
                  {items.map((item, i) => {
                    const key = `${prefix}-${i}`
                    const checked = checkedItems.has(key)
                    return (
                      <button
                        key={key}
                        onClick={() => toggleCheck(key)}
                        className="flex items-start gap-3 w-full text-left hover:bg-gray-800/50 rounded-lg px-2 py-1.5 transition-colors"
                      >
                        {checked ? (
                          <CheckSquare size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                        ) : (
                          <Square size={16} className="text-gray-600 shrink-0 mt-0.5" />
                        )}
                        <span className={`text-sm ${checked ? 'text-gray-500 line-through' : 'text-gray-300'}`}>
                          {item.replace(/^\[ \] /, '')}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : design ? (
        <div className="space-y-6">
          {/* Subtitle */}
          <div className="bg-cyan-900/20 border border-cyan-800/40 rounded-xl px-5 py-3">
            <span className="text-xs text-cyan-500 uppercase tracking-wide font-medium">Interview prompt</span>
            <p className="text-gray-300 text-sm mt-1">"{design.subtitle}"</p>
          </div>

          {/* Diagram */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-4 py-2 border-b border-gray-800 flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
              </div>
              <span className="text-xs text-gray-500 ml-1">architecture diagram</span>
            </div>
            <pre className="font-mono text-xs text-gray-300 leading-relaxed p-5 overflow-x-auto whitespace-pre">
              {design.diagram}
            </pre>
          </div>

          {/* Components */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-gray-200 text-sm">Components</h3>
            </div>
            <div className="divide-y divide-gray-800/50">
              {design.components.map((comp) => (
                <div key={comp.name} className="px-5 py-3.5">
                  <div className="font-medium text-sm text-cyan-300 mb-1">{comp.name}</div>
                  <div className="text-sm text-gray-400 leading-relaxed">{comp.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Scaling */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-gray-200 text-sm">
                Scaling Considerations
                <span className="ml-2 text-xs text-gray-500 font-normal">"How would you scale this?"</span>
              </h3>
            </div>
            <ul className="px-5 py-4 space-y-2.5">
              {design.scaling.map((item, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="text-cyan-500 font-mono text-xs mt-0.5 shrink-0">{String(i + 1).padStart(2, '0')}</span>
                  <span className="text-sm text-gray-300 leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Key decisions */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-gray-200 text-sm">Key Design Decisions</h3>
            </div>
            <ul className="px-5 py-4 space-y-2">
              {design.keyDecisions.map((d, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="text-violet-400 mt-0.5 shrink-0">▸</span>
                  <span className="text-sm text-gray-300 leading-relaxed">{d}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  )
}
