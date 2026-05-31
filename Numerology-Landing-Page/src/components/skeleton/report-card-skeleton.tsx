/** Skeleton placeholder for a report card while data loads. */
export default function ReportCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 animate-pulse">
      <div className="h-6 w-6 rounded bg-gray-200 mb-2" />
      <div className="h-4 w-28 rounded bg-gray-200 mb-1" />
      <div className="h-3 w-40 rounded bg-gray-200 mb-3" />
      <div className="h-8 w-20 rounded bg-gray-200" />
    </div>
  )
}
