/**
 * ChatStartHero — shared empty-state hero used by both:
 *   1. Welcome screen (no conversation selected)
 *   2. Active conversation with zero messages
 *
 * Renders a centered sparkle icon, heading, subhead, optional CTA, and a
 * 2-column grid of suggestion cards. Vertically centers within the
 * available scroll area so the layout never feels top-loaded.
 */

import { Sparkles } from 'lucide-react'

export interface PromptSuggestion {
  title: string
  subtitle: string
}

export const PROMPT_SUGGESTIONS: PromptSuggestion[] = [
  {
    title: 'Số chủ đạo của tôi là gì?',
    subtitle: 'Phân tích từ ngày sinh',
  },
  {
    title: 'Ý nghĩa số 7 trong thần số học',
    subtitle: 'Khám phá năng lượng & tính cách',
  },
  {
    title: 'Cách tính biểu đồ ngày sinh',
    subtitle: 'Hướng dẫn từng bước',
  },
  {
    title: 'Sự nghiệp phù hợp với số 3',
    subtitle: 'Định hướng nghề nghiệp',
  },
]

interface ChatStartHeroProps {
  heading: string
  subheading: string
  suggestions: PromptSuggestion[]
  /** Optional primary CTA below the suggestion grid (e.g. "Create conversation") */
  primaryAction?: {
    label: string
    onClick: () => void
  }
  onPickSuggestion: (text: string) => void
}

export default function ChatStartHero({
  heading,
  subheading,
  suggestions,
  primaryAction,
  onPickSuggestion,
}: ChatStartHeroProps) {
  return (
    <div className="w-full min-h-full flex items-center justify-center px-6 py-10">
      <div className="w-full max-w-2xl flex flex-col items-center text-center">
        {/* Hero icon */}
        <div
          aria-hidden="true"
          className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/30 to-primary/10 border border-primary/30 flex items-center justify-center mb-4 shadow-lg shadow-primary/10"
        >
          <Sparkles className="w-7 h-7 text-primary" />
        </div>

        {/* Heading + subhead */}
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">
          {heading}
        </h2>
        <p className="text-sm text-muted-foreground max-w-md mb-7 leading-relaxed">
          {subheading}
        </p>

        {/* Suggestion grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
          {suggestions.map((s) => (
            <button
              key={s.title}
              type="button"
              onClick={() => onPickSuggestion(s.title)}
              className="group text-left rounded-xl border border-border bg-card/60 hover:bg-card hover:border-primary/40 transition-all px-4 py-3 hover:-translate-y-0.5 hover:shadow-md hover:shadow-primary/5"
            >
              <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                {s.title}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{s.subtitle}</p>
            </button>
          ))}
        </div>

        {/* Optional CTA */}
        {primaryAction && (
          <button
            type="button"
            onClick={primaryAction.onClick}
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-primary text-primary-foreground px-5 py-2.5 text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm hover:shadow-md hover:shadow-primary/20"
          >
            <Sparkles className="w-4 h-4" aria-hidden="true" />
            {primaryAction.label}
          </button>
        )}
      </div>
    </div>
  )
}
