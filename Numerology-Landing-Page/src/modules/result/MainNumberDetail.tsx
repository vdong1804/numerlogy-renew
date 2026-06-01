import type { MainNumberIndicator } from '@/models'

import BoxContentDetail from './parts/BoxContentDetail'
import IndicatorHtml from './parts/IndicatorHtml'

export interface MainNumberDetailProps {
  /** The hero "Số Chủ Đạo" indicator with optional content_2..5. */
  indicator: MainNumberIndicator
}

/**
 * Long-form interpretation of the leading number. Renders the main content
 * plus any extra content blocks (content_2..5) when present.
 */
export default function MainNumberDetail({ indicator }: MainNumberDetailProps) {
  const extra = [
    indicator.content,
    indicator.content_2,
    indicator.content_3,
    indicator.content_4,
    indicator.content_5,
  ].filter(Boolean) as string[]

  return (
    <BoxContentDetail title="Số Chủ Đạo">
      {extra.map((html, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <IndicatorHtml key={i} html={html} />
      ))}
    </BoxContentDetail>
  )
}
