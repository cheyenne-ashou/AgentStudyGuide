'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  ArrowLeft,
  Terminal,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  AlertTriangle,
  BookOpen,
  Code2,
} from 'lucide-react'
import type { Lesson } from '@/data/lessons'
import { lessonsById } from '@/data/lessons'
import AnnotatedText from '@/components/AnnotatedText'
import { AnnotatedParagraph } from '@/components/AnnotatedText'
import CodeBlock from '@/components/CodeBlock'

type Props = { lesson: Lesson; sourceCode: string }

export default function LessonView({ lesson, sourceCode }: Props) {
  const [showSource, setShowSource] = useState(false)
  const [openConcepts, setOpenConcepts] = useState<Set<number>>(new Set([0]))

  const toggleConcept = (i: number) => {
    setOpenConcepts((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const relatedLessons = lesson.relatedIds
    .map((id) => lessonsById[id])
    .filter(Boolean)

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Back navigation */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 mb-8 transition-colors"
      >
        <ArrowLeft size={14} /> Back to Learning Path
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-500 bg-gray-800 border border-gray-700 px-2.5 py-1 rounded-full">
            {lesson.weekLabel}
          </span>
          {lesson.noApi && (
            <span className="text-xs text-emerald-400 bg-emerald-900/20 border border-emerald-800 px-2.5 py-1 rounded-full">
              No API needed
            </span>
          )}
        </div>

        <h1 className="text-3xl font-bold text-gray-100 mb-4">{lesson.title}</h1>

        {lesson.file && (
          <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-xl px-4 py-3">
            <Terminal size={14} className="text-gray-500 shrink-0" />
            <code className="text-sm font-mono text-gray-300">
              python {lesson.file}
            </code>
          </div>
        )}
      </div>

      {/* Overview */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
          Overview
        </h2>
        <p className="text-gray-200 leading-relaxed text-sm">
          <AnnotatedText text={lesson.intro} />
        </p>
      </div>

      {/* Key Concepts */}
      <div className="mb-6">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3 px-1">
          Key Concepts
        </h2>
        <div className="space-y-2">
          {lesson.concepts.map((concept, i) => {
            const isOpen = openConcepts.has(i)
            return (
              <div
                key={i}
                className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => toggleConcept(i)}
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/50 transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-violet-500 font-mono text-xs shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span className="font-medium text-gray-200 text-sm">{concept.title}</span>
                  </div>
                  {isOpen ? (
                    <ChevronUp size={15} className="text-gray-500 shrink-0" />
                  ) : (
                    <ChevronDown size={15} className="text-gray-500 shrink-0" />
                  )}
                </button>

                {isOpen && (
                  <div className="border-t border-gray-800 px-5 py-4 space-y-4">
                    <p className="text-sm text-gray-300 leading-relaxed">
                      <AnnotatedText text={concept.body} />
                    </p>
                    {concept.snippet && (
                      <div>
                        {concept.snippet.label && (
                          <div className="text-xs text-gray-500 mb-2">
                            {concept.snippet.label}
                          </div>
                        )}
                        <CodeBlock code={concept.snippet.code} language="python" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Full Source Code */}
      {sourceCode && (
        <div className="mb-6">
          <button
            onClick={() => setShowSource((s) => !s)}
            className="w-full flex items-center justify-between bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 hover:bg-gray-800/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Code2 size={16} className="text-cyan-400" />
              <span className="font-medium text-sm text-gray-200">Full Source Code</span>
              <span className="text-xs text-gray-500">{lesson.file}</span>
            </div>
            {showSource ? (
              <ChevronUp size={15} className="text-gray-500" />
            ) : (
              <ChevronDown size={15} className="text-gray-500" />
            )}
          </button>

          {showSource && (
            <div className="mt-2 rounded-xl overflow-hidden border border-gray-800">
              <CodeBlock code={sourceCode} language="python" showLineNumbers />
            </div>
          )}
        </div>
      )}

      {/* Interview Tips */}
      {lesson.interviewTips.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb size={15} className="text-yellow-400" />
            <h2 className="text-xs font-semibold text-yellow-400 uppercase tracking-widest">
              Interview Angle
            </h2>
          </div>
          <ul className="space-y-3">
            {lesson.interviewTips.map((tip, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="text-yellow-600 shrink-0 mt-0.5">▸</span>
                <span className="text-sm text-gray-300 leading-relaxed">
                  <AnnotatedParagraph text={tip} />
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Gotchas */}
      {lesson.gotchas.length > 0 && (
        <div className="bg-gray-900 border border-red-900/40 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={15} className="text-red-400" />
            <h2 className="text-xs font-semibold text-red-400 uppercase tracking-widest">
              Common Gotchas
            </h2>
          </div>
          <ul className="space-y-3">
            {lesson.gotchas.map((gotcha, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="text-red-600 shrink-0 mt-0.5">!</span>
                <span className="text-sm text-gray-300 leading-relaxed">
                  <AnnotatedText text={gotcha} />
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Related Lessons */}
      {relatedLessons.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={14} className="text-gray-500" />
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
              Related Lessons
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {relatedLessons.map((rel) => (
              <Link
                key={rel.id}
                href={`/learn/${rel.slug}`}
                className="px-4 py-2 bg-gray-900 border border-gray-700 hover:border-gray-500 rounded-xl text-sm text-gray-300 hover:text-gray-100 transition-colors"
              >
                {rel.title}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Bottom nav */}
      <div className="pt-4 border-t border-gray-800">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
        >
          <ArrowLeft size={14} /> Back to Learning Path
        </Link>
      </div>
    </div>
  )
}
