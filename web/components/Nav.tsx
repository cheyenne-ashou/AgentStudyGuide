'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Layers, MessageSquare, Cpu, BookOpen } from 'lucide-react'

const NAV_ITEMS = [
  { href: '/', label: 'Learning Path', icon: Home },
  { href: '/flashcards', label: 'Flashcards', icon: Layers },
  { href: '/questions', label: 'Q&A Practice', icon: MessageSquare },
  { href: '/system-design', label: 'System Design', icon: Cpu },
  { href: '/reference', label: 'Reference', icon: BookOpen },
]

export default function Nav() {
  const pathname = usePathname()

  return (
    <>
      {/* Sidebar — desktop */}
      <nav className="hidden md:flex flex-col fixed left-0 top-0 h-full w-56 bg-gray-900 border-r border-gray-800 px-3 py-6 z-10">
        <div className="mb-8 px-3">
          <div className="text-sm font-semibold text-violet-400 uppercase tracking-widest">
            Agentic AI
          </div>
          <div className="text-xs text-gray-500 mt-0.5">Interview Prep</div>
        </div>

        <div className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-violet-600/20 text-violet-300 font-medium'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Bottom nav — mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 z-10">
        <div className="flex justify-around py-2">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition-colors ${
                  active ? 'text-violet-400' : 'text-gray-500'
                }`}
              >
                <Icon size={18} />
                <span className="text-[10px]">{label.split(' ')[0]}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </>
  )
}
