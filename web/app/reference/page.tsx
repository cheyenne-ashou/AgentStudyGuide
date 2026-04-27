'use client'

import { useState } from 'react'
import { flashcards, CATEGORY_LABELS, CATEGORY_COLORS, type Category } from '@/data/flashcards'
import { Search, ChevronDown, ChevronUp, Tag } from 'lucide-react'
import AnnotatedText from '@/components/AnnotatedText'

export default function ReferencePage() {
  const [query, setQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<Category | 'all'>('all')
  const [expanded, setExpanded] = useState<string | null>(null)

  const categories = [...new Set(flashcards.map((c) => c.category))] as Category[]

  const filtered = flashcards.filter((card) => {
    const matchesQuery =
      !query ||
      card.term.toLowerCase().includes(query.toLowerCase()) ||
      card.definition.toLowerCase().includes(query.toLowerCase()) ||
      card.why.toLowerCase().includes(query.toLowerCase())
    const matchesCat = categoryFilter === 'all' || card.category === categoryFilter
    return matchesQuery && matchesCat
  })

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Quick Reference</h1>
        <p className="text-sm text-gray-500 mt-1">
          All {flashcards.length} terms. Search or filter, click any row for the full definition.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          placeholder="Search terms, definitions..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-violet-600 transition-colors"
        />
      </div>

      {/* Category filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategoryFilter('all')}
          className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
            categoryFilter === 'all'
              ? 'bg-violet-600/30 text-violet-300 border-violet-600'
              : 'border-gray-700 text-gray-400 hover:border-gray-500'
          }`}
        >
          All ({flashcards.length})
        </button>
        {categories.map((cat) => {
          const count = flashcards.filter((c) => c.category === cat).length
          return (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-full text-xs border transition-colors ${
                categoryFilter === cat
                  ? 'bg-violet-600/30 text-violet-300 border-violet-600'
                  : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {CATEGORY_LABELS[cat]} ({count})
            </button>
          )
        })}
      </div>

      {/* Count */}
      <div className="text-xs text-gray-600 mb-4">
        {filtered.length} term{filtered.length !== 1 ? 's' : ''}
        {query && ` matching "${query}"`}
      </div>

      {/* Terms list */}
      <div className="space-y-2">
        {filtered.map((card) => {
          const isOpen = expanded === card.id
          return (
            <div key={card.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpanded(isOpen ? null : card.id)}
                className="w-full flex items-center gap-3 px-5 py-3.5 hover:bg-gray-800/50 transition-colors text-left"
              >
                <div className="flex-1 flex items-center gap-3 min-w-0">
                  <span
                    className={`shrink-0 px-2.5 py-0.5 rounded-full text-[11px] border ${CATEGORY_COLORS[card.category]}`}
                  >
                    {CATEGORY_LABELS[card.category]}
                  </span>
                  <span className="font-medium text-sm text-gray-200 truncate">{card.term}</span>
                </div>
                {isOpen ? (
                  <ChevronUp size={15} className="text-gray-500 shrink-0" />
                ) : (
                  <ChevronDown size={15} className="text-gray-500 shrink-0" />
                )}
              </button>

              {!isOpen && (
                <div className="px-5 pb-3 -mt-1">
                  <p className="text-xs text-gray-500 line-clamp-1">
                    <AnnotatedText text={card.definition} />
                  </p>
                </div>
              )}

              {isOpen && (
                <div className="border-t border-gray-800 px-5 py-4 space-y-3">
                  <p className="text-sm text-gray-200 leading-relaxed">
                    <AnnotatedText text={card.definition} />
                  </p>
                  <div className="bg-gray-800/50 rounded-lg px-4 py-3">
                    <span className="text-xs text-gray-500 uppercase tracking-wide font-medium">Why it matters</span>
                    <p className="text-sm text-gray-300 mt-1 leading-relaxed">
                      <AnnotatedText text={card.why} />
                    </p>
                  </div>
                </div>
              )}
            </div>
          )
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500 text-sm">
            No terms match your search.
          </div>
        )}
      </div>
    </div>
  )
}
