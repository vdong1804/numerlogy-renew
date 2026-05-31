/**
 * CitationDrawer — slide-in panel from right showing citation detail.
 * Uses existing Sheet component from @radix-ui/react-dialog.
 */

import { X } from 'lucide-react'

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import type { Citation } from '@/models/Chat'

interface CitationDrawerProps {
  citation: Citation | null
  open: boolean
  onClose: () => void
}

export default function CitationDrawer({
  citation,
  open,
  onClose,
}: CitationDrawerProps) {
  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-[320px] sm:w-[380px] flex flex-col gap-0 p-0"
      >
        <SheetHeader className="px-4 py-3 border-b border-border">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-sm font-semibold">
              Nguồn trích dẫn
            </SheetTitle>
            <button
              type="button"
              aria-label="Đóng ngăn trích dẫn"
              onClick={onClose}
              className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </SheetHeader>

        {citation ? (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Index badge */}
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold bg-primary/20 text-primary">
                {citation.index}
              </span>
              <span className="text-xs text-muted-foreground uppercase tracking-wide">
                {citation.sourceType}
              </span>
            </div>

            {/* Title */}
            {citation.title && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  Tiêu đề
                </p>
                <p className="text-sm font-semibold leading-snug">
                  {citation.title}
                </p>
              </div>
            )}

            {/* Relevance score */}
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">
                Độ liên quan
              </p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${Math.round(citation.score * 100)}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {Math.round(citation.score * 100)}%
                </span>
              </div>
            </div>

            {/* Chunk ID (debug reference) */}
            <div className="rounded-md bg-muted/50 px-3 py-2">
              <p className="text-xs text-muted-foreground">
                Đoạn văn #{citation.chunkId}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <p className="text-sm text-muted-foreground text-center">
              Nhấn vào số trích dẫn <span className="font-semibold">[N]</span>{' '}
              trong câu trả lời để xem nguồn.
            </p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}
