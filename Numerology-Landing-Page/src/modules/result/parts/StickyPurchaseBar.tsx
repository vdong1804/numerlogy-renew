import { Box, Button, Container, Typography } from '@mui/material'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'

import { listProducts, type Product } from '@/lib/shop-api'
import { formatVnd } from '@/lib/utils'

/**
 * Bottom sticky upsell bar for free viewers on /ket-qua.
 *
 * Shows the suggested "full report" product (first report-type product) + its
 * price, and deep-links to /shop/[slug]. The user's name/birthday already live in
 * the customerInfo store, so the product form prefills there (no re-entry).
 *
 * Renders nothing when no report product is configured or the fetch fails — it
 * must never break the result page.
 */
export default function StickyPurchaseBar() {
  const router = useRouter()
  const [product, setProduct] = useState<Product | null>(null)

  useEffect(() => {
    let alive = true
    listProducts('report')
      .then((items) => {
        if (alive) setProduct(items[0] ?? null)
      })
      .catch(() => {
        /* best-effort upsell — ignore failures */
      })
    return () => {
      alive = false
    }
  }, [])

  if (!product) return null

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1200,
        py: 1.5,
        borderTop: '1px solid rgba(68, 187, 255, 0.25)',
        backgroundColor: 'rgba(1, 22, 37, 0.92)',
        backdropFilter: 'blur(10px)',
      }}
    >
      <Container maxWidth={false}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'stretch', sm: 'center' },
            justifyContent: 'space-between',
            gap: 1.5,
          }}
        >
          <Box>
            <Typography sx={{ fontWeight: 600, fontSize: '1rem' }}>
              Mở khóa toàn bộ luận giải — {product.name}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              Xem đầy đủ chỉ số cốt lõi, đỉnh cao, thử thách & tải file PDF chi tiết.
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              justifyContent: { xs: 'space-between', sm: 'flex-end' },
            }}
          >
            <Typography
              component="span"
              sx={{ fontWeight: 700, fontSize: '1.25rem', color: '#44BBFF' }}
            >
              {product.price === 0 ? 'Miễn phí' : formatVnd(product.price)}
            </Typography>
            <Button
              variant="contained"
              onClick={() => router.push(`/shop/${product.slug}`)}
            >
              Mở khóa ngay
            </Button>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
