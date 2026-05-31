/**
 * Admin product create page.
 * Route: /admin/products/new
 */
import { useRouter } from 'next/router'
import { z } from 'zod'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader } from '@/components/admin/admin-page-header'
import GenericCrudForm from '@/components/admin/generic-crud-form'
import type { FieldDef } from '@/components/admin/generic-crud-form'
import { toast } from '@/components/admin/admin-toast'
import { postJson } from '@/lib/admin-api'

const schema = z.object({
  sku: z.string().min(1, 'Bắt buộc'),
  type: z.enum(['package', 'report', 'combo']),
  name: z.string().min(1, 'Bắt buộc'),
  slug: z.string().min(1, 'Bắt buộc'),
  description: z.string().optional(),
  price: z.number().min(0),
  quota: z.number().optional().nullable(),
  renewal_days: z.number().optional().nullable(),
  template_name: z.string().optional(),
  sort_order: z.number(),
})

type ProductForm = z.infer<typeof schema>

const FIELDS: FieldDef<ProductForm>[] = [
  { name: 'sku', label: 'SKU', required: true, placeholder: 'VD: report-overview' },
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
  { name: 'name', label: 'Tên sản phẩm', required: true, placeholder: 'VD: Báo cáo Tổng quan' },
  { name: 'slug', label: 'Slug URL', required: true, placeholder: 'bao-cao-tong-quan' },
  { name: 'description', label: 'Mô tả', type: 'textarea' },
  { name: 'price', label: 'Giá (VND)', type: 'number', placeholder: '99000' },
  { name: 'quota', label: 'Quota (chỉ cho gói)', type: 'number', helperText: 'Số báo cáo tải được' },
  { name: 'renewal_days', label: 'Số ngày hiệu lực (chỉ cho gói)', type: 'number' },
  { name: 'template_name', label: 'Template (chỉ cho báo cáo)', placeholder: 'report-overview.html' },
  { name: 'sort_order', label: 'Thứ tự hiển thị', type: 'number' },
]

export default function ProductNewPage() {
  const router = useRouter()

  const handleSubmit = async (data: ProductForm) => {
    // Normalize empty optional numbers to null for backend
    const payload = {
      ...data,
      quota: data.quota || null,
      renewal_days: data.renewal_days || null,
      template_name: data.template_name || null,
      description: data.description || null,
    }
    await postJson('/admin/products', payload)
    toast.success('Đã tạo sản phẩm')
    router.push('/admin/products')
  }

  return (
    <AdminLayout title="Tạo sản phẩm">
      <AdminPageHeader
        title="Tạo sản phẩm"
        description="Thêm gói, báo cáo lẻ hoặc combo vào catalogue"
        backHref="/admin/products"
      />
      <GenericCrudForm schema={schema} fields={FIELDS} onSubmit={handleSubmit} submitLabel="Tạo sản phẩm" />
    </AdminLayout>
  )
}
