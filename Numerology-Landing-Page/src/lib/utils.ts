/**
 * Shared admin utilities: class merge helper + formatters.
 */
import clsx from 'clsx'
import type { ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatVnd(n: number | null | undefined) {
  if (n == null) return '—'
  return `${n.toLocaleString('vi-VN')} ₫`
}

export function formatDateVi(d: string | Date | null | undefined) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('vi-VN')
}

export function formatDateTimeVi(d: string | Date | null | undefined) {
  if (!d) return '—'
  return new Date(d).toLocaleString('vi-VN')
}
