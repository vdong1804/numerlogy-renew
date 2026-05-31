/**
 * Admin content create page.
 * Route: /admin/content/[resource]/new
 */
import { useRouter } from 'next/router'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader } from '@/components/admin/admin-page-header'
import ContentForm from '@/components/admin/content-form'
import type { ContentFormValues } from '@/components/admin/content-form'
import { toast } from '@/components/admin/admin-toast'
import { Skeleton } from '@/components/ui/skeleton'
import { postJson } from '@/lib/admin-api'
import { findResource } from '@/lib/content-resources'

export default function ContentNewPage() {
  const router = useRouter()
  const resource = router.query.resource as string
  const resourceMeta = resource ? findResource(resource) : undefined

  const handleSubmit = async (data: ContentFormValues) => {
    await postJson(`/admin/content/${resource}`, data)
    toast.success('Đã tạo bản ghi mới')
    router.push(`/admin/content/${resource}`)
  }

  if (!resourceMeta) {
    return (
      <AdminLayout title="Tạo bản ghi">
        <Skeleton className="h-64 w-full max-w-3xl" />
      </AdminLayout>
    )
  }

  return (
    <AdminLayout title={`Tạo ${resourceMeta.label}`}>
      <AdminPageHeader
        title={`Tạo mới · ${resourceMeta.label}`}
        description={`Slug: ${resource}`}
        backHref={`/admin/content/${resource}`}
      />
      <ContentForm resource={resourceMeta} onSubmit={handleSubmit} submitLabel="Tạo bản ghi" />
    </AdminLayout>
  )
}
