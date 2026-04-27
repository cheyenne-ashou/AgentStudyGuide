import type { Metadata } from 'next'
import './globals.css'
import Nav from '@/components/Nav'

export const metadata: Metadata = {
  title: 'Agentic AI Study',
  description: 'Interactive interview prep for agentic AI engineering roles',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-[#0a0a0f] text-gray-100 min-h-screen">
        <Nav />
        {/* Offset for sidebar on desktop, padding-bottom for mobile nav */}
        <main className="md:ml-56 pb-20 md:pb-0 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
