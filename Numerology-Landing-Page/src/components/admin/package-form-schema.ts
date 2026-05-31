/**
 * Shared zod schema + TypeScript type for admin package create/edit forms.
 * Validates chat_addon fields only when package_kind === 'chat_addon'.
 */
import { z } from 'zod'

export const PACKAGE_KIND_OPTIONS = [
  { value: 'pdf_download', label: 'PDF Download' },
  { value: 'chat_addon', label: 'Chat AI Add-on' },
] as const

export const TIER_OPTIONS = [
  { value: 'pro', label: 'Pro (chất lượng cao)' },
  { value: 'flash', label: 'Flash (miễn phí)' },
] as const

export const packageFormSchema = z
  .object({
    name: z.string().min(1, 'Bắt buộc'),
    price: z.number().min(0),
    price_sale: z.number().min(0),
    number_download: z.number().min(0),
    content: z.string().optional(),
    package_kind: z
      .enum(['pdf_download', 'chat_addon'])
      .default('pdf_download'),
    // chat_addon-only — validated conditionally below
    message_count: z
      .number()
      .int()
      .min(1, 'Phải là số nguyên dương')
      .nullable()
      .optional(),
    tier: z.enum(['flash', 'pro']).nullable().optional(),
    validity_days: z
      .number()
      .int()
      .min(1, 'Phải là số nguyên dương')
      .nullable()
      .optional(),
  })
  .superRefine((val, ctx) => {
    if (val.package_kind !== 'chat_addon') return
    if (!val.message_count || val.message_count < 1) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Bắt buộc với gói Chat AI',
        path: ['message_count'],
      })
    }
    if (!val.tier) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Bắt buộc với gói Chat AI',
        path: ['tier'],
      })
    }
    if (!val.validity_days || val.validity_days < 1) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Bắt buộc với gói Chat AI',
        path: ['validity_days'],
      })
    }
  })

export type PackageFormValues = z.infer<typeof packageFormSchema>

/** Strip chat_addon-only fields when kind=pdf_download before posting. */
export function preparePayload(
  data: PackageFormValues
): Record<string, unknown> {
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { message_count, tier, validity_days, ...base } = data
  if (data.package_kind === 'chat_addon') {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    return { ...base, message_count, tier, validity_days }
  }
  // pdf_download — omit addon fields entirely (don't send nulls)
  return base
}
