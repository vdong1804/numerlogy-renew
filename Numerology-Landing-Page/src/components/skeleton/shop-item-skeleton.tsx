/** Skeleton placeholder for a shop product card while data loads. */
export default function ShopItemSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 animate-pulse">
      <div className="h-40 w-full rounded-lg bg-gray-200 mb-3" />
      <div className="h-4 w-3/4 rounded bg-gray-200 mb-2" />
      <div className="h-3 w-1/2 rounded bg-gray-200 mb-3" />
      <div className="flex items-center justify-between">
        <div className="h-5 w-20 rounded bg-gray-200" />
        <div className="h-8 w-24 rounded bg-gray-200" />
      </div>
    </div>
  )
}
