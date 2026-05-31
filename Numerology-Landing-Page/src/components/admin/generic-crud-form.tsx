/**
 * Generic CRUD form for simple resources (news, packages, banks).
 * Supports arbitrary field definitions + optional RichText field.
 */
import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import type { DefaultValues, FieldValues, Path } from 'react-hook-form'
import type { ZodType } from 'zod'
import { AlertCircle, CheckCircle2, Save } from 'lucide-react'

import RichTextEditor from './rich-text-editor'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'
import { Textarea } from '@/components/ui/textarea'

export interface FieldDef<T extends FieldValues> {
  name: Path<T>
  label: string
  type?: 'text' | 'number' | 'textarea' | 'richtext' | 'select'
  options?: { value: string; label: string }[]
  required?: boolean
  placeholder?: string
  helperText?: string
}

interface GenericCrudFormProps<T extends FieldValues> {
  schema: ZodType<T>
  fields: FieldDef<T>[]
  initialData?: Partial<T>
  onSubmit: (data: T) => Promise<void>
  submitLabel?: string
}

export default function GenericCrudForm<T extends FieldValues>({
  schema,
  fields,
  initialData,
  onSubmit,
  submitLabel = 'Lưu thay đổi',
}: GenericCrudFormProps<T>) {
  const [error, setError] = React.useState('')
  const [success, setSuccess] = React.useState(false)

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<T>({
    resolver: zodResolver(schema),
    defaultValues: (initialData ?? {}) as DefaultValues<T>,
  })

  const submit = async (data: T) => {
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
    <Card className="max-w-3xl">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit(submit)} className="space-y-5">
          {fields.map((f) => (
            <div key={String(f.name)} className="space-y-2">
              <Label htmlFor={String(f.name)}>
                {f.label}
                {f.required && <span className="text-destructive ml-0.5">*</span>}
              </Label>

              {f.type === 'richtext' ? (
                <Controller
                  name={f.name}
                  control={control}
                  render={({ field }) => (
                    <RichTextEditor
                      value={(field.value as string) ?? ''}
                      onChange={field.onChange}
                    />
                  )}
                />
              ) : f.type === 'select' ? (
                <NativeSelect id={String(f.name)} {...register(f.name)}>
                  <option value="">-- Chọn --</option>
                  {f.options?.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </NativeSelect>
              ) : f.type === 'textarea' ? (
                <Textarea
                  id={String(f.name)}
                  placeholder={f.placeholder}
                  {...register(f.name)}
                />
              ) : (
                <Input
                  id={String(f.name)}
                  type={f.type === 'number' ? 'number' : 'text'}
                  placeholder={f.placeholder}
                  {...register(f.name, { ...(f.type === 'number' ? { valueAsNumber: true } : {}) })}
                />
              )}

              {f.helperText && (
                <p className="text-xs text-muted-foreground">{f.helperText}</p>
              )}
              {errors[f.name] && (
                <p className="text-xs text-destructive">
                  {String((errors[f.name] as { message?: string })?.message ?? 'Lỗi')}
                </p>
              )}
            </div>
          ))}

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
