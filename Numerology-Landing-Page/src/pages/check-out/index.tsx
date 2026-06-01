/**
 * /check-out (no orderId) — legacy placeholder.
 *
 * The real checkout flow lives at `/check-out/[orderId]` (driven by SePay).
 * This page exists only because users may have an old bookmark; immediately
 * redirect to the shop so they can start a real order.
 */
import { useRouter } from 'next/router'
import { useEffect } from 'react'

import type { NextPageWithLayout } from '@/models'

const CheckoutFallback: NextPageWithLayout = () => {
  const router = useRouter()
  useEffect(() => {
    router.replace('/shop')
  }, [router])
  return null
}

export default CheckoutFallback
