'use client'

import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

type Props = {
  code: string
  language?: string
  showLineNumbers?: boolean
}

export default function CodeBlock({ code, language = 'python', showLineNumbers = false }: Props) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="relative group rounded-xl overflow-hidden">
      {/* Copy button */}
      <button
        onClick={copy}
        className="absolute top-3 right-3 z-10 p-1.5 rounded-lg bg-gray-700/80 hover:bg-gray-600 opacity-0 group-hover:opacity-100 transition-all"
      >
        {copied ? (
          <Check size={13} className="text-emerald-400" />
        ) : (
          <Copy size={13} className="text-gray-300" />
        )}
      </button>

      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        showLineNumbers={showLineNumbers}
        customStyle={{
          margin: 0,
          padding: '1.25rem',
          background: '#1e1e2e',
          fontSize: '0.8rem',
          lineHeight: '1.6',
          borderRadius: 0,
        }}
        lineNumberStyle={{
          color: '#4b5563',
          minWidth: '2.5rem',
          paddingRight: '1rem',
          userSelect: 'none',
        }}
      >
        {code.trim()}
      </SyntaxHighlighter>
    </div>
  )
}
