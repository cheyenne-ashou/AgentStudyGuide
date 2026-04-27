'use client'

import React from 'react'
import Tooltip from './Tooltip'
import { glossary } from '@/data/glossary'

// Build sorted term list (longest-first to prevent partial matches)
const SORTED_TERMS = Object.keys(glossary).sort((a, b) => b.length - a.length)

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

type Segment =
  | { type: 'text'; value: string }
  | { type: 'term'; matched: string; key: string }

function findSegments(text: string): Segment[] {
  type Match = { start: number; end: number; matched: string; key: string }
  const matches: Match[] = []

  for (const term of SORTED_TERMS) {
    const pattern = new RegExp(`\\b${escapeRegex(term)}\\b`, 'gi')
    let m: RegExpExecArray | null
    while ((m = pattern.exec(text)) !== null) {
      const start = m.index
      const end = start + m[0].length
      // Skip if overlaps with an existing match
      if (!matches.some((x) => start < x.end && end > x.start)) {
        matches.push({ start, end, matched: m[0], key: term })
      }
    }
  }

  matches.sort((a, b) => a.start - b.start)

  const segments: Segment[] = []
  let pos = 0
  for (const { start, end, matched, key } of matches) {
    if (pos < start) segments.push({ type: 'text', value: text.slice(pos, start) })
    segments.push({ type: 'term', matched, key })
    pos = end
  }
  if (pos < text.length) segments.push({ type: 'text', value: text.slice(pos) })
  return segments
}

type Props = {
  text: string
  className?: string
}

/**
 * Renders a plain text string, wrapping known glossary terms in tooltip underlines.
 * Safe to use in any inline context (p, span, li, etc.).
 */
export default function AnnotatedText({ text, className }: Props) {
  const segments = findSegments(text)

  return (
    <span className={className}>
      {segments.map((seg, i) => {
        if (seg.type === 'text') return seg.value
        const entry = glossary[seg.key]
        return (
          <Tooltip
            key={i}
            term={seg.matched}
            definition={entry.short}
            example={entry.example}
          >
            {seg.matched}
          </Tooltip>
        )
      })}
    </span>
  )
}

/**
 * Renders a paragraph that handles **bold**, `code`, and glossary annotations.
 * For use inside Q&A answers and other markdown-lite text.
 */
export function AnnotatedParagraph({ text }: { text: string }) {
  // Split by inline code first (preserve as-is)
  const codeChunks = text.split(/(`[^`\n]+`)/g)

  return (
    <>
      {codeChunks.map((chunk, ci) => {
        if (chunk.startsWith('`') && chunk.endsWith('`') && chunk.length > 2) {
          return (
            <code
              key={ci}
              className="font-mono text-xs bg-gray-800 px-1 py-0.5 rounded text-violet-300"
            >
              {chunk.slice(1, -1)}
            </code>
          )
        }
        // Handle **bold** within non-code chunks
        const boldChunks = chunk.split(/(\*\*[^*\n]+\*\*)/g)
        return boldChunks.map((bc, bi) => {
          if (bc.startsWith('**') && bc.endsWith('**') && bc.length > 4) {
            const inner = bc.slice(2, -2)
            return (
              <strong key={`${ci}-${bi}`} className="text-gray-100 font-semibold">
                <AnnotatedText text={inner} />
              </strong>
            )
          }
          return <AnnotatedText key={`${ci}-${bi}`} text={bc} />
        })
      })}
    </>
  )
}
