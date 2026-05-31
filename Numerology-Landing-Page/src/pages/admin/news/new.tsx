/**
 * Admin news create page.
 * Route: /admin/news/new
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
  title: z.string().min(1, 'Bắt buộc'),
  short_content: z.string().optional(),
  content: z.string().min(1, 'Bắt buộc'),
  category: z.number().optional(),
  image: z.string().optional(),
})

type NewsForm = z.infer<typeof schema>

const FIELDS: FieldDef<NewsForm>[] = [
  { name: 'title', label: 'Tiêu đề', required: true, placeholder: 'Tiêu đề bài viết' },
  { name: 'short_content', label: 'Tóm tắt', type: 'textarea', placeholder: 'Mô tả ngắn...' },
  { name: 'content', label: 'Nội dung', type: 'richtext' },
  { name: 'category', label: 'Danh mục (số)', type: 'number' },
  { name: 'image', label: 'URL ảnh đại diện', placeholder: 'https://...' },
]

export default function NewsNewPage() {
  const router = useRouter()

  const handleSubmit = async (data: NewsForm) => {
    await postJson('/admin/news', data)
    toast.success('Đã tạo tin tức mới')
    router.push('/admin/news')
  }

  return (
    <AdminLayout title="Tạo tin tức">
      <AdminPageHeader
        title="Tạo tin tức mới"
        description="Soạn bài viết và lưu vào hệ thống"
        backHref="/admin/news"
      />
      <GenericCrudForm schema={schema} fields={FIELDS} onSubmit={handleSubmit} submitLabel="Tạo tin tức" />
    </AdminLayout>
  )
}
