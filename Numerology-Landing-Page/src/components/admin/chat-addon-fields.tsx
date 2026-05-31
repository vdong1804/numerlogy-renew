/**
 * Shared fieldset for chat_addon package fields.
 * Rendered conditionally when package_kind === 'chat_addon'.
 */
import * as React from 'react'
import type { Control, FieldErrors } from 'react-hook-form'
import { Controller } from 'react-hook-form'

import type { PackageFormValues } from '@/components/admin/package-form-schema'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect } from '@/components/ui/native-select'

interface ChatAddonFieldsProps {
  control: Control<PackageFormValues>
  errors: FieldErrors<PackageFormValues>
}

export default function ChatAddonFields({
  control,
  errors,
}: ChatAddonFieldsProps) {
  return (
    <fieldset className="space-y-4 rounded-md border border-border p-4">
      <legend className="px-1 text-sm font-semibold text-muted-foreground">
        Thông tin gói Chat AI
      </legend>

      {/* message_count */}
      <div className="space-y-1.5">
        <Label htmlFor="message_count">
          Số tin nhắn<span className="text-destructive ml-0.5">*</span>
        </Label>
        <Controller
          name="message_count"
          control={control}
          render={({ field }) => (
            <Input
              id="message_count"
              type="number"
              min={1}
              placeholder="VD: 100"
              value={field.value ?? ''}
              onChange={(e) =>
                field.onChange(
                  e.target.value === '' ? null : Number(e.target.value)
                )
              }
            />
          )}
        />
        {errors.message_count && (
          <p className="text-xs text-destructive">
            {errors.message_count.message}
          </p>
        )}
      </div>

      {/* tier */}
      <div className="space-y-1.5">
        <Label htmlFor="tier">
          Hạng (model)<span className="text-destructive ml-0.5">*</span>
        </Label>
        <Controller
          name="tier"
          control={control}
          render={({ field }) => (
            <NativeSelect
              id="tier"
              value={field.value ?? ''}
              onChange={field.onChange}
            >
              <option value="pro">Pro (chất lượng cao)</option>
              <option value="flash">Flash (miễn phí)</option>
            </NativeSelect>
          )}
        />
        <p className="text-xs text-muted-foreground">
          Pro = Gemini 2.5 Pro (chất lượng cao). Flash = Gemini 2.0 Flash (miễn
          phí).
        </p>
        {errors.tier && (
          <p className="text-xs text-destructive">{errors.tier.message}</p>
        )}
      </div>

      {/* validity_days */}
      <div className="space-y-1.5">
        <Label htmlFor="validity_days">
          Số ngày hiệu lực<span className="text-destructive ml-0.5">*</span>
        </Label>
        <Controller
          name="validity_days"
          control={control}
          render={({ field }) => (
            <Input
              id="validity_days"
              type="number"
              min={1}
              placeholder="VD: 30"
              value={field.value ?? ''}
              onChange={(e) =>
                field.onChange(
                  e.target.value === '' ? null : Number(e.target.value)
                )
              }
            />
          )}
        />
        {errors.validity_days && (
          <p className="text-xs text-destructive">
            {errors.validity_days.message}
          </p>
        )}
      </div>
    </fieldset>
  )
}
