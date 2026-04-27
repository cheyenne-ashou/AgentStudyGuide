'use client'

import { useState, useRef, useEffect } from 'react'

type Props = {
  children: React.ReactNode
  term: string
  definition: string
  example: string
}

export default function Tooltip({ children, term, definition, example }: Props) {
  const [visible, setVisible] = useState(false)
  const [above, setAbove] = useState(true)
  const ref = useRef<HTMLSpanElement>(null)

  // Decide whether to show tooltip above or below based on space
  const handleMouseEnter = () => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect()
      setAbove(rect.top > 200)
    }
    setVisible(true)
  }

  return (
    <span
      ref={ref}
      className="relative inline"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setVisible(false)}
    >
      {/* Underlined trigger word */}
      <span className="border-b border-dotted border-gray-400/70 cursor-help">
        {children}
      </span>

      {/* Tooltip popup */}
      {visible && (
        <span
          className={`
            absolute z-50 w-72 rounded-xl border border-gray-600 bg-gray-800 shadow-2xl p-3.5
            pointer-events-none select-none
            ${above ? 'bottom-6 left-0' : 'top-6 left-0'}
          `}
          style={{ minWidth: '260px' }}
        >
          {/* Term */}
          <span className="block text-xs font-semibold text-violet-400 mb-1.5">{term}</span>

          {/* Definition */}
          <span className="block text-xs text-gray-200 leading-relaxed">{definition}</span>

          {/* Example */}
          {example && (
            <span className="block text-[11px] text-gray-400 mt-2 pt-2 border-t border-gray-700 leading-relaxed italic">
              {example}
            </span>
          )}
        </span>
      )}
    </span>
  )
}
