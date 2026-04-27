import fs from 'fs'
import path from 'path'
import { notFound } from 'next/navigation'
import { lessonsBySlug } from '@/data/lessons'
import LessonView from '@/components/LessonView'

type Props = { params: Promise<{ slug: string }> }

export default async function LessonPage({ params }: Props) {
  const { slug } = await params
  const lesson = lessonsBySlug[slug]
  if (!lesson) notFound()

  let sourceCode = ''
  if (lesson.file) {
    try {
      // web/ is one level inside agentic/, so go up one level
      const filePath = path.join(process.cwd(), '..', lesson.file)
      sourceCode = fs.readFileSync(filePath, 'utf-8')
    } catch {
      sourceCode = `# Could not read file: ${lesson.file}\n# Make sure the agentic/ directory is at the expected location.`
    }
  }

  return <LessonView lesson={lesson} sourceCode={sourceCode} />
}

export async function generateStaticParams() {
  const { lessons } = await import('@/data/lessons')
  return lessons.map((l) => ({ slug: l.slug }))
}
