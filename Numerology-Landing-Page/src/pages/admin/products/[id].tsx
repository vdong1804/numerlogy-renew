/**
 * Admin product edit page.
 * Route: /admin/products/[id]
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
  sku: z.string().min(1, 'Bắt buộc'),
  type: z.enum(['package', 'report', 'combo']),
  name: z.string().min(1, 'Bắt buộc'),
  slug: z.string().min(1, 'Bắt buộc'),
  description: z.string().optional().nullable(),
  price: z.number().min(0),
  quota: z.number().optional().nullable(),
  renewal_days: z.number().optional().nullable(),
  template_name: z.string().optional().nullable(),
  sort_order: z.number(),
})

type ProductForm = z.infer<typeof schema>

const FIELDS: FieldDef<ProductForm>[] = [
  { name: 'sku', label: 'SKU', required: true },
  {
    name: 'type',
    label: 'Loại',
    type: 'select',
    required: true,
    options: [
      { value: 'package', label: 'Gói thuê bao' },
      { value: 'report', label: 'Báo cáo lẻ' },
      { value: 'combo', label: 'Combo' },
    ],
  },
  { name: 'name', label: 'Tên sản phẩm', required: true },
  { name: 'slug', label: 'Slug URL', required: true },
  { name: 'description', label: 'Mô tả', type: 'textarea' },
  { name: 'price', label: 'Giá (VND)', type: 'number' },
  { name: 'quota', label: 'Quota', type: 'number' },
  { name: 'renewal_days', label: 'Số ngày hiệu lực', type: 'number' },
  { name: 'template_name', label: 'Template' },
  { name: 'sort_order', label: 'Thứ tự hiển thị', type: 'number' },
]

export default function ProductEditPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [initialData, setInitialData] = useState<Partial<ProductForm> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!id) return
    getJson<ProductForm>(`/admin/products/${id}`)
      .then((d) => setInitialData(d))
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSubmit = async (data: ProductForm) => {
    const payload = {
      ...data,
      quota: data.quota || null,
      renewal_days: data.renewal_days || null,
      template_name: data.template_name || null,
      description: data.description || null,
    }
    await putJson(`/admin/products/${id}`, payload)
    toast.success('Đã lưu thay đổi')
    router.push('/admin/products')
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await del(`/admin/products/${id}`)
      toast.success('Đã xóa sản phẩm')
      router.push('/admin/products')
    } catch (err) {
      toast.error((err as Error).message)
      setShowDelete(false)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <AdminLayout title={`Sửa sản phẩm #${id}`}>
      <AdminPageHeader
        title={`Sản phẩm #${id}`}
        description="Cập nhật thông tin"
        backHref="/admin/products"
      >
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
        <div className="space-y-3 max-w-3xl">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-24 w-full" />
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
        title="Xóa sản phẩm"
        message={`Xác nhận xóa sản phẩm #${id}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </AdminLayout>
  )
}
