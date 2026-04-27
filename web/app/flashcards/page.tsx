'use client'

import { useState, useEffect, useCallback } from 'react'
import { flashcards, CATEGORY_LABELS, CATEGORY_COLORS, type Category, type Flashcard } from '@/data/flashcards'
import { RotateCcw, ChevronLeft, ChevronRight, Shuffle, Check, RefreshCw, Tag } from 'lucide-react'
import AnnotatedText from '@/components/AnnotatedText'

type Status = 'unseen' | 'known' | 'review'

const STATUS_STYLES: Record<Status, string> = {
  unseen: 'text-gray-500',
  known: 'text-emerald-400',
  review: 'text-yellow-400',
}

function shuffle<T>(arr: T[]): T[] {
  return [...arr].sort(() => Math.random() - 0.5)
}

export default function FlashcardsPage() {
  const [categoryFilter, setCategoryFilter] = useState<Category | 'all'>('all')
  const [statuses, setStatuses] = useState<Record<string, Status>>({})
  const [deck, setDeck] = useState<Flashcard[]>(flashcards)
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [reviewOnly, setReviewOnly] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('flashcard-statuses')
    if (stored) setStatuses(JSON.parse(stored))
  }, [])

  const saveStatus = (id: string, status: Status) => {
    const next = { ...statuses, [id]: status }
    setStatuses(next)
    localStorage.setItem('flashcard-statuses', JSON.stringify(next))
  }

  const filteredCards = deck.filter((c) => {
    if (reviewOnly) return statuses[c.id] === 'review' || statuses[c.id] === 'unseen'
    if (categoryFilter === 'all') return true
    return c.category === categoryFilter
  })

  const current = filteredCards[index] ?? null
  const knownCount = flashcards.filter((c) => statuses[c.id] === 'known').length
  const reviewCount = flashcards.filter((c) => statuses[c.id] === 'review').length

  const go = useCallback(
    (dir: 1 | -1) => {
      setIndex((i) => {
        const n = (i + dir + filteredCards.length) % filteredCards.length
        return n
      })
      setFlipped(false)
    },
    [filteredCards.length]
  )

  const doShuffle = () => {
    setDeck(shuffle(flashcards))
    setIndex(0)
    setFlipped(false)
  }

  const resetAll = () => {
    setStatuses({})
    localStorage.removeItem('flashcard-statuses')
    setIndex(0)
    setFlipped(false)
  }

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') go(1)
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key === ' ') { e.preventDefault(); setFlipped((f) => !f) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [go])

  const categories = [...new Set(flashcards.map((c) => c.category))] as Category[]

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Flashcards</h1>
          <p className="text-sm text-gray-500 mt-1">
            {knownCount} known · {reviewCount} to review · {flashcards.length} total
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={doShuffle}
            className="flex items-center gap-1.5 px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            <Shuffle size={13} /> Shuffle
          </button>
          <button
            onClick={resetAll}
            className="flex items-center gap-1.5 px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            <RefreshCw size={13} /> Reset
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="h-2 rounded-full bg-emerald-500 transition-all"
            style={{ width: `${(knownCount / flashcards.length) * 100}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-1">
          <span>Known: {knownCount}/{flashcards.length}</span>
          <span>Card {filteredCards.length > 0 ? index + 1 : 0}/{filteredCards.length}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => { setCategoryFilter('all'); setIndex(0); setFlipped(false) }}
          className={`px-3 py-1 rounded-full text-xs border transition-colors ${
            categoryFilter === 'all' && !reviewOnly
              ? 'bg-violet-600/30 text-violet-300 border-violet-600'
              : 'border-gray-700 text-gray-400 hover:border-gray-500'
          }`}
        >
          All
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => { setCategoryFilter(cat); setReviewOnly(false); setIndex(0); setFlipped(false) }}
            className={`px-3 py-1 rounded-full text-xs border transition-colors ${
              categoryFilter === cat && !reviewOnly
                ? 'bg-violet-600/30 text-violet-300 border-violet-600'
                : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            {CATEGORY_LABELS[cat]}
          </button>
        ))}
        <button
          onClick={() => { setReviewOnly((r) => !r); setIndex(0); setFlipped(false) }}
          className={`px-3 py-1 rounded-full text-xs border transition-colors ${
            reviewOnly
              ? 'bg-yellow-600/30 text-yellow-300 border-yellow-600'
              : 'border-gray-700 text-gray-400 hover:border-gray-500'
          }`}
        >
          To Review
        </button>
      </div>

      {/* Card */}
      {current ? (
        <div className="flip-container" style={{ height: 320 }}>
          <div
            className={`flip-card cursor-pointer w-full h-full`}
            style={{
              transformStyle: 'preserve-3d',
              transition: 'transform 0.5s cubic-bezier(0.4,0,0.2,1)',
              transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
              position: 'relative',
            }}
            onClick={() => setFlipped((f) => !f)}
          >
            {/* Front */}
            <div
              className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 border border-gray-700 rounded-2xl p-8 select-none"
              style={{ backfaceVisibility: 'hidden' }}
            >
              <div className={`mb-4 px-3 py-1 rounded-full text-xs border ${CATEGORY_COLORS[current.category]}`}>
                <Tag size={10} className="inline mr-1" />
                {CATEGORY_LABELS[current.category]}
              </div>
              <h2 className="text-2xl font-bold text-center text-gray-100 mb-3">{current.term}</h2>
              <p className="text-sm text-gray-500 text-center">Click to reveal definition</p>
            </div>

            {/* Back */}
            <div
              className="absolute inset-0 flex flex-col justify-between bg-gray-900 border border-violet-800/50 rounded-2xl p-7 select-none"
              style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
            >
              <div>
                <h3 className="font-semibold text-violet-400 text-sm mb-3">{current.term}</h3>
                <p className="text-gray-200 text-sm leading-relaxed mb-4">
                  <AnnotatedText text={current.definition} />
                </p>
                <div className="border-t border-gray-800 pt-3">
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Why it matters</span>
                  <p className="text-gray-400 text-sm mt-1 leading-relaxed">
                    <AnnotatedText text={current.why} />
                  </p>
                </div>
              </div>
              <div className="text-xs text-gray-600 text-center">Click to flip back</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-80 flex items-center justify-center bg-gray-900 border border-gray-800 rounded-2xl">
          <p className="text-gray-500">No cards match this filter.</p>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => go(-1)}
          disabled={!current}
          className="flex items-center gap-1.5 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm text-gray-300 disabled:opacity-40 transition-colors"
        >
          <ChevronLeft size={16} /> Prev
        </button>

        <div className="flex gap-2">
          <button
            onClick={() => { if (current) { saveStatus(current.id, 'review'); go(1) } }}
            disabled={!current}
            className="px-4 py-2.5 bg-yellow-900/30 hover:bg-yellow-900/50 text-yellow-400 rounded-xl text-sm transition-colors disabled:opacity-40"
          >
            Review Later
          </button>
          <button
            onClick={() => { if (current) { saveStatus(current.id, 'known'); go(1) } }}
            disabled={!current}
            className="flex items-center gap-1.5 px-4 py-2.5 bg-emerald-900/30 hover:bg-emerald-900/50 text-emerald-400 rounded-xl text-sm transition-colors disabled:opacity-40"
          >
            <Check size={14} /> Known
          </button>
        </div>

        <button
          onClick={() => go(1)}
          disabled={!current}
          className="flex items-center gap-1.5 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-xl text-sm text-gray-300 disabled:opacity-40 transition-colors"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>

      <p className="text-center text-xs text-gray-600 mt-4">
        Space to flip · ← → to navigate
      </p>
    </div>
  )
}
