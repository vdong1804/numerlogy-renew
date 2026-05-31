/**
 * Admin bank edit page.
 * Route: /admin/banks/[id]
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
  bank: z.string().min(1, 'Bắt buộc'),
  account_number: z.string().min(1, 'Bắt buộc'),
  account_holder: z.string().min(1, 'Bắt buộc'),
  branch: z.string().optional(),
  image: z.string().optional(),
  code: z.string().optional(),
})

type BankForm = z.infer<typeof schema>

const FIELDS: FieldDef<BankForm>[] = [
  { name: 'bank', label: 'Tên ngân hàng', required: true },
  { name: 'account_number', label: 'Số tài khoản', required: true },
  { name: 'account_holder', label: 'Chủ tài khoản', required: true },
  { name: 'branch', label: 'Chi nhánh' },
  { name: 'image', label: 'URL ảnh QR' },
  { name: 'code', label: 'Mã ngân hàng' },
]

export default function BankEditPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [initialData, setInitialData] = useState<Partial<BankForm> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    getJson<BankForm>(`/admin/banks/${id}`)
      .then((d) => setInitialData(d))
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSubmit = async (data: BankForm) => {
    await putJson(`/admin/banks/${id}`, data)
    toast.success('Đã lưu thay đổi')
    router.push('/admin/banks')
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await del(`/admin/banks/${id}`)
      toast.success('Đã xóa ngân hàng')
      router.push('/admin/banks')
    } catch (err) {
      toast.error((err as Error).message)
      setShowDelete(false)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <AdminLayout title={`Sửa ngân hàng #${id}`}>
      <AdminPageHeader title={`Ngân hàng #${id}`} description="Chỉnh sửa thông tin tài khoản" backHref="/admin/banks">
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
        <Skeleton className="h-72 w-full max-w-3xl" />
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
        title="Xóa ngân hàng"
        message={`Xác nhận xóa ngân hàng #${id}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </AdminLayout>
  )
}
