/**
 * Admin content edit/delete page.
 * Route: /admin/content/[resource]/[id]
 */
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import ContentForm from '@/components/admin/content-form'
import type { ContentFormValues } from '@/components/admin/content-form'
import { toast } from '@/components/admin/admin-toast'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { del, getJson, putJson } from '@/lib/admin-api'
import { findResource } from '@/lib/content-resources'

export default function ContentEditPage() {
  const router = useRouter()
  const resource = router.query.resource as string
  const id = router.query.id as string

  const [initialData, setInitialData] = useState<Partial<ContentFormValues> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const resourceMeta = resource ? findResource(resource) : undefined

  useEffect(() => {
    if (!resource || !id) return
    setLoading(true)
    getJson<ContentFormValues>(`/admin/content/${resource}/${id}`)
      .then((data) => setInitialData(data))
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [resource, id])

  const handleSubmit = async (data: ContentFormValues) => {
    await putJson(`/admin/content/${resource}/${id}`, data)
    toast.success('Đã lưu thay đổi')
    router.push(`/admin/content/${resource}`)
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await del(`/admin/content/${resource}/${id}`)
      toast.success('Đã xóa bản ghi')
      router.push(`/admin/content/${resource}`)
    } catch (err) {
      toast.error((err as Error).message)
      setShowDelete(false)
    } finally {
      setDeleting(false)
    }
  }

  const label = resourceMeta?.label ?? resource

  return (
    <AdminLayout title={`Sửa ${label}`}>
      <AdminPageHeader
        title={`${label} · #${id}`}
        description={`Slug: ${resource}`}
        backHref={`/admin/content/${resource}`}
      >
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={() => setShowDelete(true)}
        >
          <Trash2 className="w-4 h-4" /> Xóa bản ghi
        </Button>
      </AdminPageHeader>

      <ErrorBanner message={error} />

      {loading ? (
        <Skeleton className="h-96 w-full max-w-4xl" />
      ) : (
        initialData &&
        resourceMeta && (
          <ContentForm
            resource={resourceMeta}
            initialData={initialData}
            onSubmit={handleSubmit}
            submitLabel="Lưu thay đổi"
          />
        )
      )}

      <ConfirmDialog
        open={showDelete}
        title="Xóa bản ghi"
        message={`Xác nhận xóa bản ghi #${id} của ${label}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </AdminLayout>
  )
}
