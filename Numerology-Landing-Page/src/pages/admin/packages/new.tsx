/**
 * Admin package create page.
 * Route: /admin/packages/new
 * Supports pdf_download (default) and chat_addon kinds.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, CheckCircle2, Save } from 'lucide-react'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader } from '@/components/admin/admin-page-header'
import { toast } from '@/components/admin/admin-toast'
import ChatAddonFields from '@/components/admin/chat-addon-fields'
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
import { Textarea } from '@/components/ui/textarea'
import { postJson } from '@/lib/admin-api'

export default function PackageNewPage() {
  const router = useRouter()
  const [submitError, setSubmitError] = useState('')
  const [success, setSuccess] = useState(false)

  const {
    register,
    control,
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

  const onSubmit = async (data: PackageFormValues) => {
    setSubmitError('')
    setSuccess(false)
    try {
      await postJson('/admin/packages', preparePayload(data))
      toast.success('Đã tạo gói dịch vụ')
      setSuccess(true)
      router.push('/admin/packages')
    } catch (err) {
      setSubmitError((err as Error).message)
    }
  }

  return (
    <AdminLayout title="Tạo gói dịch vụ">
      <AdminPageHeader
        title="Tạo gói dịch vụ"
        description="Cấu hình giá và quota"
        backHref="/admin/packages"
      />
      <Card className="max-w-3xl">
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* name */}
            <div className="space-y-1.5">
              <Label htmlFor="name">
                Tên gói<span className="text-destructive ml-0.5">*</span>
              </Label>
              <Input
                id="name"
                placeholder="VD: Gói Cơ Bản"
                {...register('name')}
              />
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
                placeholder="99000"
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
                placeholder="79000"
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

            {/* number_download — only shown for pdf_download */}
            {packageKind !== 'chat_addon' && (
              <div className="space-y-1.5">
                <Label htmlFor="number_download">Số lượt tải</Label>
                <Input
                  id="number_download"
                  type="number"
                  placeholder="5"
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
              <Textarea
                id="content"
                placeholder="Mô tả gói dịch vụ..."
                {...register('content')}
              />
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
                {isSubmitting ? 'Đang lưu...' : 'Tạo gói'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </AdminLayout>
  )
}
