/**
 * Payment client — public bank receiver info for SePay transfers.
 *
 * GET /api/payments/bank returns the bank account details displayed in
 * the SePayPaymentBlock component. No auth required (display-only data).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000'

export interface BankInfo {
  account_number: string
  account_holder: string
  bank_code: string
  bank_name: string
}

export async function getBankInfo(): Promise<BankInfo> {
  const res = await fetch(`${API_BASE}/api/payments/bank`)
  if (!res.ok) throw new Error(`Failed to load bank info: ${res.statusText}`)
  return res.json() as Promise<BankInfo>
}
