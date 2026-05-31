/**
 * Sub-components for content-form field groups.
 * Keeps content-form.tsx under 200 lines.
 */
import * as React from 'react'
import type { UseFormRegister, FieldErrors, Control } from 'react-hook-form'
import { Controller } from 'react-hook-form'

import RichTextEditor from './rich-text-editor'
import type { ContentFormValues } from './content-form'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface BaseFieldsProps {
  register: UseFormRegister<ContentFormValues>
  errors: FieldErrors<ContentFormValues>
}

function FieldWrap({
  htmlFor,
  label,
  required,
  helper,
  error,
  children,
}: {
  htmlFor: string
  label: string
  required?: boolean
  helper?: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>
        {label}
        {required && <span className="text-destructive ml-0.5">*</span>}
      </Label>
      {children}
      {helper && <p className="text-xs text-muted-foreground">{helper}</p>}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

/** code + value + title + number_page */
export function BaseFields({ register, errors }: BaseFieldsProps) {
  return (
    <>
      <FieldWrap htmlFor="code" label="Code" required error={errors.code?.message as string | undefined}>
        <Input
          id="code"
          {...register('code', { required: 'Bắt buộc' })}
          placeholder="Ví dụ: 1, 2, 11..."
        />
      </FieldWrap>

      <FieldWrap htmlFor="value" label="Value" helper="Giá trị kỹ thuật (tuỳ chọn)">
        <Input id="value" {...register('value')} placeholder="Giá trị kỹ thuật" />
      </FieldWrap>

      <FieldWrap htmlFor="title" label="Tiêu đề">
        <Input id="title" {...register('title')} placeholder="Tiêu đề hiển thị" />
      </FieldWrap>

      <FieldWrap htmlFor="number_page" label="Số trang">
        <Input
          id="number_page"
          type="number"
          className="max-w-[160px]"
          {...register('number_page', { valueAsNumber: true })}
        />
      </FieldWrap>
    </>
  )
}

interface RichFieldProps {
  name: keyof ContentFormValues
  label: string
  control: Control<ContentFormValues>
}

/** Single rich-text field using Controller */
export function RichField({ name, label, control }: RichFieldProps) {
  return (
    <FieldWrap htmlFor={String(name)} label={label}>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <RichTextEditor
            value={(field.value as string) ?? ''}
            onChange={field.onChange}
          />
        )}
      />
    </FieldWrap>
  )
}

/** phone-master-data: only code + bow */
export function PhoneMasterFields({ register, errors }: BaseFieldsProps) {
  return (
    <>
      <FieldWrap htmlFor="code" label="Code" required error={errors.code?.message as string | undefined}>
        <Input id="code" {...register('code', { required: 'Bắt buộc' })} placeholder="Đầu số" />
      </FieldWrap>

      <FieldWrap htmlFor="bow" label="Bow">
        <Input id="bow" {...(register('bow' as keyof ContentFormValues) as React.InputHTMLAttributes<HTMLInputElement>)} placeholder="Bow value" />
      </FieldWrap>
    </>
  )
}
