/**
 * Shared admin utilities: class merge helper + formatters.
 */
import type { ClassValue } from 'clsx'
import clsx from 'clsx'
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

/**
 * Compact Vietnamese relative time: "vừa xong", "5 phút", "2 giờ", "3 ngày", or date.
 * Used for conversation list timestamps.
 */
export function formatRelativeVi(d: string | Date | null | undefined) {
  if (!d) return ''
  const date = typeof d === 'string' ? new Date(d) : d
  const diff = Date.now() - date.getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return 'vừa xong'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min} phút`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} giờ`
  const day = Math.floor(hr / 24)
  if (day < 7) return `${day} ngày`
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}
