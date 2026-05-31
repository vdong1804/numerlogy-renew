/**
 * Admin news edit page.
 * Route: /admin/news/[id]
 */
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import { z } from 'zod'
import { Trash2 } from 'lucide-react'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader, ErrorBanner } from '@/components/admin/admin-page-header'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import GenericCrudForm from '@/components/admin/generic-crud-form'
import type { FieldDef } from '@/components/admin/generic-crud-form'
import { toast } from '@/components/admin/admin-toast'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { del, getJson, putJson } from '@/lib/admin-api'

const schema = z.object({
  title: z.string().min(1, 'Bắt buộc'),
  short_content: z.string().optional(),
  content: z.string().optional(),
  category: z.number().optional(),
  image: z.string().optional(),
})

type NewsForm = z.infer<typeof schema>

const FIELDS: FieldDef<NewsForm>[] = [
  { name: 'title', label: 'Tiêu đề', required: true },
  { name: 'short_content', label: 'Tóm tắt', type: 'textarea' },
  { name: 'content', label: 'Nội dung', type: 'richtext' },
  { name: 'category', label: 'Danh mục (số)', type: 'number' },
  { name: 'image', label: 'URL ảnh đại diện' },
]

export default function NewsEditPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [initialData, setInitialData] = useState<Partial<NewsForm> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    getJson<NewsForm>(`/admin/news/${id}`)
      .then((d) => setInitialData(d))
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSubmit = async (data: NewsForm) => {
    await putJson(`/admin/news/${id}`, data)
    toast.success('Đã cập nhật tin tức')
    router.push('/admin/news')
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await del(`/admin/news/${id}`)
      toast.success('Đã xóa tin tức')
      router.push('/admin/news')
    } catch (err) {
      toast.error((err as Error).message)
      setShowDelete(false)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <AdminLayout title={`Sửa tin tức #${id}`}>
      <AdminPageHeader title={`Tin tức #${id}`} description="Cập nhật bài viết" backHref="/admin/news">
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={() => setShowDelete(true)}
        >
          <Trash2 className="w-4 h-4" /> Xóa
        </Button>
      </AdminPageHeader>

      <ErrorBanner message={error} />

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-9 w-full max-w-3xl" />
          <Skeleton className="h-24 w-full max-w-3xl" />
          <Skeleton className="h-48 w-full max-w-3xl" />
        </div>
      ) : (
        initialData && (
          <GenericCrudForm
            schema={schema}
            fields={FIELDS}
            initialData={initialData}
            onSubmit={handleSubmit}
            submitLabel="Lưu thay đổi"
          />
        )
      )}

      <ConfirmDialog
        open={showDelete}
        title="Xóa tin tức"
        message={`Xác nhận xóa tin tức #${id}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </AdminLayout>
  )
}
