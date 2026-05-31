/**
 * Generic content CRUD form.
 * Supports: standard fields + RichText content, main-number (content_2..5), phone-master-data.
 * Uses react-hook-form + Zod validation.
 */
import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { AlertCircle, CheckCircle2, Save } from 'lucide-react'

import type { ContentResource } from '@/lib/content-resources'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

import { BaseFields, PhoneMasterFields, RichField } from './content-form-fields'

const schema = z.object({
  code: z.string().min(1, 'Bắt buộc'),
  value: z.string().optional(),
  title: z.string().optional(),
  content: z.string().optional(),
  content_2: z.string().optional(),
  content_3: z.string().optional(),
  content_4: z.string().optional(),
  content_5: z.string().optional(),
  number_page: z.number().optional(),
  bow: z.string().optional(),
})

export type ContentFormValues = z.infer<typeof schema>

interface ContentFormProps {
  resource: ContentResource
  initialData?: Partial<ContentFormValues>
  onSubmit: (data: ContentFormValues) => Promise<void>
  submitLabel?: string
}

export default function ContentForm({
  resource,
  initialData,
  onSubmit,
  submitLabel = 'Lưu thay đổi',
}: ContentFormProps) {
  const [error, setError] = React.useState('')
  const [success, setSuccess] = React.useState(false)

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ContentFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      code: '',
      value: '',
      title: '',
      content: '',
      content_2: '',
      content_3: '',
      content_4: '',
      content_5: '',
      number_page: undefined,
      bow: '',
      ...initialData,
    },
  })

  const submit = async (data: ContentFormValues) => {
    setError('')
    setSuccess(false)
    try {
      await onSubmit(data)
      setSuccess(true)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <Card className="max-w-4xl">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit(submit)} className="space-y-5">
          {resource.isPhoneMaster ? (
            <PhoneMasterFields register={register} errors={errors} />
          ) : (
            <>
              <BaseFields register={register} errors={errors} />
              <RichField name="content" label="Nội dung" control={control} />
              {resource.hasExtraContent && (
                <>
                  <RichField name="content_2" label="Nội dung 2" control={control} />
                  <RichField name="content_3" label="Nội dung 3" control={control} />
                  <RichField name="content_4" label="Nội dung 4" control={control} />
                  <RichField name="content_5" label="Nội dung 5" control={control} />
                </>
              )}
            </>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
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
              {isSubmitting ? 'Đang lưu...' : submitLabel}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
