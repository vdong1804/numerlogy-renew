/**
 * Admin chatbot KB manager — list + upload PDF/DOCX/TXT documents.
 * Route: /admin/chatbot/kb
 */
import { useCallback, useEffect, useState } from 'react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import { getJson } from '@/lib/admin-api'
import KbDocumentList from '@/modules/admin/chatbot/kb-document-list'
import KbUploadForm from '@/modules/admin/chatbot/kb-upload-form'
import type { KbDocumentListResponse } from '@/modules/admin/chatbot/chatbot-types'

const PAGE_SIZE = 20

export default function ChatbotKbPage() {
  const [data, setData] = useState<KbDocumentListResponse | null>(null)
  const [pageIndex, setPageIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(pageIndex * PAGE_SIZE),
      })
      const resp = await getJson<KbDocumentListResponse>(
        `/admin/chatbot/kb/documents?${params}`
      )
      setData(resp)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [pageIndex])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <AdminLayout title="Knowledge Base">
      <AdminPageHeader
        title="Knowledge Base"
        description="Quản lý tài liệu được ingest vào RAG: PDF / DOCX / TXT / MD"
      />
      <ErrorBanner message={error} />

      <section className="mb-6">
        <KbUploadForm onUploaded={() => fetchData()} />
      </section>

      <KbDocumentList
        rows={data?.items ?? []}
        total={data?.total ?? 0}
        loading={loading}
        pageIndex={pageIndex}
        pageSize={PAGE_SIZE}
        onPaginationChange={(pi) => setPageIndex(pi)}
        onDeleted={fetchData}
      />
    </AdminLayout>
  )
}
