/**
 * Admin package edit page.
 * Route: /admin/packages/[id]
 * Supports pdf_download and chat_addon kinds with conditional fieldset.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, CheckCircle2, Save, Trash2 } from 'lucide-react'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

import AdminLayout from '@/components/admin/admin-layout'
import {
  AdminPageHeader,
  ErrorBanner,
} from '@/components/admin/admin-page-header'
import { toast } from '@/components/admin/admin-toast'
import ChatAddonFields from '@/components/admin/chat-addon-fields'
import ConfirmDialog from '@/components/admin/confirm-dialog'
import {
  type PackageFormValues,
  PACKAGE_KIND_OPTIONS,
  packageFormSchema,
  preparePayload,
} from '@/components/admin/package-form-schema'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { del, getJson, putJson } from '@/lib/admin-api'

export default function PackageEditPage() {
  const router = useRouter()
  const id = router.query.id as string
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitError, setSubmitError] = useState('')
  const [success, setSuccess] = useState(false)
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const {
    register,
    control,
    reset,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PackageFormValues>({
    resolver: zodResolver(packageFormSchema),
    defaultValues: {
      package_kind: 'pdf_download',
      price: 0,
      price_sale: 0,
      number_download: 0,
      tier: 'pro',
      validity_days: 30,
    },
  })

  const packageKind = useWatch({ control, name: 'package_kind' })

  useEffect(() => {
    if (!id) return
    getJson<PackageFormValues>(`/admin/packages/${id}`)
      .then((d) =>
        reset({
          name: d.name ?? '',
          price: d.price ?? 0,
          price_sale: d.price_sale ?? 0,
          number_download: d.number_download ?? 0,
          content: d.content ?? '',
          package_kind: d.package_kind ?? 'pdf_download',
          message_count: d.message_count ?? null,
          tier: d.tier ?? 'pro',
          validity_days: d.validity_days ?? 30,
        })
      )
      .catch((err) => setLoadError((err as Error).message))
      .finally(() => setLoading(false))
  }, [id, reset])

  const onSubmit = async (data: PackageFormValues) => {
    setSubmitError('')
    setSuccess(false)
    try {
      await putJson(`/admin/packages/${id}`, preparePayload(data))
      toast.success('Đã lưu thay đổi')
      setSuccess(true)
      router.push('/admin/packages')
    } catch (err) {
      setSubmitError((err as Error).message)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await del(`/admin/packages/${id}`)
      toast.success('Đã xóa gói dịch vụ')
      router.push('/admin/packages')
    } catch (err) {
      toast.error((err as Error).message)
      setShowDelete(false)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <AdminLayout title={`Sửa gói #${id}`}>
      <AdminPageHeader
        title={`Gói dịch vụ #${id}`}
        description="Cập nhật thông tin gói"
        backHref="/admin/packages"
      >
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={() => setShowDelete(true)}
        >
          <Trash2 className="w-4 h-4" /> Xóa
        </Button>
      </AdminPageHeader>
      <ErrorBanner message={loadError} />

      {loading ? (
        <div className="space-y-3 max-w-3xl">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <Card className="max-w-3xl">
          <CardContent className="p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* name */}
              <div className="space-y-1.5">
                <Label htmlFor="name">
                  Tên gói<span className="text-destructive ml-0.5">*</span>
                </Label>
                <Input id="name" {...register('name')} />
                {errors.name && (
                  <p className="text-xs text-destructive">
                    {errors.name.message}
                  </p>
                )}
              </div>

              {/* package_kind */}
              <div className="space-y-1.5">
                <Label htmlFor="package_kind">Loại gói</Label>
                <NativeSelect id="package_kind" {...register('package_kind')}>
                  {PACKAGE_KIND_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </NativeSelect>
                {errors.package_kind && (
                  <p className="text-xs text-destructive">
                    {errors.package_kind.message}
                  </p>
                )}
              </div>

              {/* price */}
              <div className="space-y-1.5">
                <Label htmlFor="price">Giá (VNĐ)</Label>
                <Input
                  id="price"
                  type="number"
                  {...register('price', { valueAsNumber: true })}
                />
                {errors.price && (
                  <p className="text-xs text-destructive">
                    {errors.price.message}
                  </p>
                )}
              </div>

              {/* price_sale */}
              <div className="space-y-1.5">
                <Label htmlFor="price_sale">Giá khuyến mãi (VNĐ)</Label>
                <Input
                  id="price_sale"
                  type="number"
                  {...register('price_sale', { valueAsNumber: true })}
                />
                <p className="text-xs text-muted-foreground">
                  Đặt 0 nếu không có khuyến mãi
                </p>
                {errors.price_sale && (
                  <p className="text-xs text-destructive">
                    {errors.price_sale.message}
                  </p>
                )}
              </div>

              {/* number_download — only for pdf_download */}
              {packageKind !== 'chat_addon' && (
                <div className="space-y-1.5">
                  <Label htmlFor="number_download">Số lượt tải</Label>
                  <Input
                    id="number_download"
                    type="number"
                    {...register('number_download', { valueAsNumber: true })}
                  />
                  {errors.number_download && (
                    <p className="text-xs text-destructive">
                      {errors.number_download.message}
                    </p>
                  )}
                </div>
              )}

              {/* content */}
              <div className="space-y-1.5">
                <Label htmlFor="content">Mô tả</Label>
                <Textarea id="content" {...register('content')} />
                {errors.content && (
                  <p className="text-xs text-destructive">
                    {errors.content.message}
                  </p>
                )}
              </div>

              {/* chat_addon conditional fieldset */}
              {packageKind === 'chat_addon' && (
                <ChatAddonFields control={control} errors={errors} />
              )}

              {submitError && (
                <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{submitError}</span>
                </div>
              )}
              {success && (
                <div className="flex items-start gap-2 rounded-md border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
                  <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>Đã lưu thành công!</span>
                </div>
              )}

              <div className="flex items-center justify-end pt-2 border-t border-border">
                <Button type="submit" size="lg" disabled={isSubmitting}>
                  <Save className="w-4 h-4" />
                  {isSubmitting ? 'Đang lưu...' : 'Lưu thay đổi'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={showDelete}
        title="Xóa gói dịch vụ"
        message={`Xác nhận xóa gói #${id}? Hành động này không thể hoàn tác.`}
        confirmLabel="Xóa vĩnh viễn"
        danger
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDelete(false)}
      />
    </AdminLayout>
  )
}
