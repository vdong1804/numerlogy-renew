/**
 * Admin bank create page.
 * Route: /admin/banks/new
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
  bank: z.string().min(1, 'Bắt buộc'),
  account_number: z.string().min(1, 'Bắt buộc'),
  account_holder: z.string().min(1, 'Bắt buộc'),
  branch: z.string().optional(),
  image: z.string().optional(),
  code: z.string().optional(),
})

type BankForm = z.infer<typeof schema>

const FIELDS: FieldDef<BankForm>[] = [
  { name: 'bank', label: 'Tên ngân hàng', required: true, placeholder: 'VD: Vietcombank' },
  { name: 'account_number', label: 'Số tài khoản', required: true, placeholder: '1234567890' },
  { name: 'account_holder', label: 'Chủ tài khoản', required: true, placeholder: 'NGUYEN VAN A' },
  { name: 'branch', label: 'Chi nhánh', placeholder: 'Hà Nội' },
  { name: 'image', label: 'URL ảnh QR', placeholder: 'https://...' },
  { name: 'code', label: 'Mã ngân hàng', placeholder: 'VCB' },
]

export default function BankNewPage() {
  const router = useRouter()

  const handleSubmit = async (data: BankForm) => {
    await postJson('/admin/banks', data)
    toast.success('Đã thêm ngân hàng')
    router.push('/admin/banks')
  }

  return (
    <AdminLayout title="Thêm ngân hàng">
      <AdminPageHeader title="Thêm ngân hàng" description="Tạo tài khoản nhận thanh toán mới" backHref="/admin/banks" />
      <GenericCrudForm schema={schema} fields={FIELDS} onSubmit={handleSubmit} submitLabel="Tạo ngân hàng" />
    </AdminLayout>
  )
}
