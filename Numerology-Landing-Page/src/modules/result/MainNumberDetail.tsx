import type { MainNumberIndicator } from '@/models'

import BoxContentDetail from './parts/BoxContentDetail'
import IndicatorHtml from './parts/IndicatorHtml'
import LockOverlay from './parts/LockOverlay'

export interface MainNumberDetailProps {
  /** The hero "Số Chủ Đạo" indicator with optional content_2..5. */
  indicator: MainNumberIndicator
}

/**
 * Long-form interpretation of the leading number. Renders the main content
 * plus any extra content blocks (content_2..5) when present. When the deep-dive
 * facets are gated (`extra_locked`) the backend strips them and we show an
 * unlock teaser instead.
 */
export default function MainNumberDetail({ indicator }: MainNumberDetailProps) {
  const blocks = [
    indicator.content,
    indicator.content_2,
    indicator.content_3,
    indicator.content_4,
    indicator.content_5,
  ].filter(Boolean) as string[]

  return (
    <BoxContentDetail title="Số Chủ Đạo">
      {indicator.locked ? (
        <LockOverlay hint="Luận giải số chủ đạo dành cho báo cáo đầy đủ" />
      ) : (
        blocks.map((html, i) => (
          // eslint-disable-next-line react/no-array-index-key
          <IndicatorHtml key={i} html={html} />
        ))
      )}
      {!indicator.locked && indicator.extra_locked && (
        <LockOverlay hint="Còn nhiều luận giải chuyên sâu (sự nghiệp, tình yêu...) trong báo cáo đầy đủ" />
      )}
    </BoxContentDetail>
  )
}
