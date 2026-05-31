/**
 * Shop catalogue page — /shop
 * Lists all active products filtered by type tab.
 */
import { useEffect, useMemo, useState } from 'react'
import type { ReactElement } from 'react'

import CatalogueTabs, { type CatalogueTabValue } from '@/components/shop/catalogue-tabs'
import ProductCard from '@/components/shop/product-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import { listProducts, type Product } from '@/lib/shop-api'

const ShopPage: NextPageWithLayout = () => {
  const [tab, setTab] = useState<CatalogueTabValue>('all')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    const filter = tab === 'all' ? undefined : tab
    listProducts(filter)
      .then(setProducts)
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [tab])

  const visible = useMemo(() => products, [products])

  return (
    <div className="account-shell min-h-[70vh]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <header className="mb-6 text-center sm:text-left">
          <div className="flex items-center gap-2 sm:justify-start justify-center">
            <span className="inline-block w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(249,106,45,0.55)]" />
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Cửa hàng</h1>
          </div>
          <div className="h-[3px] w-14 bg-primary rounded-full mt-2 mx-auto sm:mx-0" />
          <p className="text-sm text-muted-foreground mt-3">
            Chọn gói báo cáo phù hợp với hành trình khám phá bản thân của bạn.
          </p>
        </header>

        <CatalogueTabs value={tab} onChange={setTab} />

        {error && (
          <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md px-4 py-2 mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-56 w-full rounded-xl" />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-card p-12 text-center">
            <p className="text-sm text-muted-foreground">
              Chưa có sản phẩm trong danh mục này.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pb-12">
            {visible.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

ShopPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main meta={<Meta title="Cửa hàng" description="Mua gói báo cáo Thần Số Học" />}>
      {page}
    </Main>
  )
}

export default ShopPage
