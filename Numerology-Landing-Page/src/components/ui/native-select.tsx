/**
 * Native styled select — lightweight alternative to Radix Select.
 * Sufficient for admin forms (no search, no virtual list needed).
 */
import * as React from 'react'
import { ChevronDown } from 'lucide-react'

import { cn } from '@/lib/utils'

export interface NativeSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const NativeSelect = React.forwardRef<HTMLSelectElement, NativeSelectProps>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          'flex h-9 w-full appearance-none rounded-md border border-input bg-background pl-3 pr-8 py-1 text-sm shadow-sm ' +
            'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ' +
            'focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
    </div>
  )
)
NativeSelect.displayName = 'NativeSelect'

export { NativeSelect }
