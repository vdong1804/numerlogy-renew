/**
 * Cookie consent banner — NĐ 13/2023 compliance.
 * Blocks GA4 + Meta Pixel until user explicitly accepts analytics/marketing.
 * State stored in localStorage via consent-storage lib.
 */
import { useEffect, useState } from 'react'

import {
  clearConsent,
  getConsent,
  hasValidConsent,
  setConsent,
  type ConsentState,
} from '@/lib/consent-storage'

interface CookieConsentProps {
  onConsentChange?: (state: ConsentState) => void
}

type View = 'banner' | 'customize' | 'hidden'

export default function CookieConsent({ onConsentChange }: CookieConsentProps) {
  const [view, setView] = useState<View>('hidden')
  const [analytics, setAnalytics] = useState(false)
  const [marketing, setMarketing] = useState(false)

  useEffect(() => {
    // Show banner only if no valid consent stored
    if (!hasValidConsent()) {
      setView('banner')
    }
  }, [])

  const save = (state: Omit<ConsentState, 'timestamp'>) => {
    const saved = setConsent(state)
    onConsentChange?.(saved)
    setView('hidden')
    // Fire analytics load if newly accepted — page reload not needed,
    // Analytics component listens via storage event.
    window.dispatchEvent(new Event('nsq_consent_updated'))
  }

  const acceptAll = () => save({ analytics: true, marketing: true })

  const rejectAll = () => save({ analytics: false, marketing: false })

  const saveCustom = () => save({ analytics, marketing })

  if (view === 'hidden') return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        background: '#1a1a2e',
        color: '#e0e0e0',
        padding: '16px 20px',
        boxShadow: '0 -2px 12px rgba(0,0,0,0.3)',
        fontFamily: 'inherit',
        fontSize: '14px',
      }}
    >
      {view === 'banner' && (
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <p style={{ flex: 1, minWidth: '240px', margin: 0, lineHeight: 1.5 }}>
            Chúng tôi sử dụng cookie để cải thiện trải nghiệm của bạn và đo lường
            hiệu quả quảng cáo. Xem{' '}
            <a href="/privacy" style={{ color: '#a78bfa', textDecoration: 'underline' }}>
              Chính sách bảo mật
            </a>{' '}
            để biết thêm.
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setView('customize')}
              style={btnStyle('outline')}
            >
              Tuỳ chỉnh
            </button>
            <button onClick={rejectAll} style={btnStyle('outline')}>
              Từ chối
            </button>
            <button onClick={acceptAll} style={btnStyle('primary')}>
              Chấp nhận tất cả
            </button>
          </div>
        </div>
      )}

      {view === 'customize' && (
        <div style={{ maxWidth: '560px', margin: '0 auto' }}>
          <p style={{ fontWeight: 600, marginBottom: '12px' }}>Tuỳ chỉnh cookie</p>
          <label style={checkboxRow}>
            <input type="checkbox" checked disabled readOnly />
            <span>
              <strong>Thiết yếu</strong> — bắt buộc để site hoạt động
            </span>
          </label>
          <label style={checkboxRow}>
            <input
              type="checkbox"
              checked={analytics}
              onChange={(e) => setAnalytics(e.target.checked)}
            />
            <span>
              <strong>Phân tích</strong> — Google Analytics 4 (ẩn danh)
            </span>
          </label>
          <label style={checkboxRow}>
            <input
              type="checkbox"
              checked={marketing}
              onChange={(e) => setMarketing(e.target.checked)}
            />
            <span>
              <strong>Marketing</strong> — Meta Pixel (nhắm mục tiêu quảng cáo)
            </span>
          </label>
          <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
            <button onClick={() => setView('banner')} style={btnStyle('outline')}>
              Quay lại
            </button>
            <button onClick={saveCustom} style={btnStyle('primary')}>
              Lưu tuỳ chỉnh
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Inline style helpers to avoid tailwind dependency in this component
const btnStyle = (variant: 'primary' | 'outline'): React.CSSProperties => ({
  padding: '8px 16px',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '13px',
  fontWeight: 500,
  border: variant === 'primary' ? 'none' : '1px solid #6b7280',
  background: variant === 'primary' ? '#7c3aed' : 'transparent',
  color: '#fff',
  whiteSpace: 'nowrap',
})

const checkboxRow: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '10px',
  marginBottom: '10px',
  cursor: 'pointer',
  lineHeight: 1.4,
}
