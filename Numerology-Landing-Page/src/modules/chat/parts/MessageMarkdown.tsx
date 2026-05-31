/**
 * MessageMarkdown — renders assistant markdown with sanitization.
 * [N] tokens in text become clickable citation spans.
 * Sanitizes via rehype-sanitize (blocks <script>, <iframe>).
 */

import React, { useMemo } from 'react'
import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'

interface MessageMarkdownProps {
  content: string
  onCitationClick: (index: number) => void
}

/** Replace [N] patterns with a special marker the paragraph renderer handles */
function transformCitationTokens(
  text: string,
  onCitationClick: (n: number) => void
): React.ReactNode[] {
  const parts = text.split(/(\[\d+\])/g)
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/)
    if (match) {
      // match[1] is guaranteed by the regex /^\[(\d+)\]$/ — non-null assertion is safe here
      const n = parseInt(match[1]!, 10)
      return (
        <button
          key={i}
          type="button"
          aria-label={`Xem trích dẫn ${n}`}
          onClick={() => onCitationClick(n)}
          className="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold bg-primary/20 text-primary hover:bg-primary/40 transition-colors cursor-pointer mx-0.5 leading-none"
        >
          {n}
        </button>
      )
    }
    return part
  })
}

export default function MessageMarkdown({
  content,
  onCitationClick,
}: MessageMarkdownProps) {
  const components: Components = useMemo(
    () => ({
      p({ children }) {
        const processNode = (node: React.ReactNode): React.ReactNode => {
          if (typeof node === 'string') {
            return transformCitationTokens(node, onCitationClick)
          }
          return node
        }
        const processed = React.Children.map(children, processNode)
        return <p className="mb-2 last:mb-0 leading-relaxed">{processed}</p>
      },
      code({ children, className }) {
        const isBlock = className?.startsWith('language-')
        if (isBlock) {
          return (
            <pre className="rounded-md bg-muted p-3 overflow-x-auto text-sm my-2">
              <code>{children}</code>
            </pre>
          )
        }
        return (
          <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">
            {children}
          </code>
        )
      },
      ul({ children }) {
        return <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>
      },
      ol({ children }) {
        return <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>
      },
      li({ children }) {
        return <li className="text-sm leading-relaxed">{children}</li>
      },
      strong({ children }) {
        return <strong className="font-semibold">{children}</strong>
      },
    }),
    [onCitationClick]
  )

  return (
    <div className="prose prose-sm max-w-none text-foreground text-sm">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
