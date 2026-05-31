/** Skeleton placeholder for an order row while data loads. */
export default function OrderCardSkeleton() {
  return (
    <div className="w-full rounded-xl border border-border p-4 animate-pulse">
      <div className="flex items-center justify-between gap-4">
        <div className="h-4 w-32 rounded bg-gray-200" />
        <div className="h-4 w-20 rounded bg-gray-200" />
        <div className="h-4 w-24 rounded bg-gray-200" />
        <div className="h-4 w-28 rounded bg-gray-200" />
      </div>
    </div>
  )
}
