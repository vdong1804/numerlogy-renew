/**
 * Toast container — Sonner mount for admin notifications.
 * Re-exports `toast` for use in pages.
 */
import * as React from 'react'
import { Toaster, toast } from 'sonner'
import { useTheme } from 'next-themes'

export function ToastProvider() {
  const { resolvedTheme } = useTheme()
  return (
    <Toaster
      theme={(resolvedTheme as 'light' | 'dark') ?? 'light'}
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-popover group-[.toaster]:text-popover-foreground ' +
            'group-[.toaster]:border-border group-[.toaster]:shadow-lg group-[.toaster]:rounded-lg',
          description: 'group-[.toast]:text-muted-foreground',
          actionButton:
            'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
          cancelButton:
            'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
        },
      }}
    />
  )
}

export { toast }
