/**
 * Type definitions for the data-driven numerology report
 * (GET /api/numerology-report). Content fields are HTML strings
 * rendered via dangerouslySetInnerHTML; many may be null → guard them.
 */

/** A single numerology indicator (one number + its interpretation). */
export interface NumerologyIndicator {
  code: number | string
  title: string | null
  content: string | null
  number_page?: number | null
  /**
   * Entitlement gating (server-driven). When true the viewer is NOT entitled to
   * this section: `content` is stripped server-side (null) and the UI shows a
   * lock-card teaser instead. Free interpretations never ship locked content.
   */
  locked?: boolean
}

/** Hero "Số Chủ Đạo" indicator: may carry extra content blocks 2..5. */
export interface MainNumberIndicator extends NumerologyIndicator {
  /** Compound display form, e.g. "13/4" or "22/4" (G6). */
  compound?: string
  content_2?: string | null
  content_3?: string | null
  content_4?: string | null
  content_5?: string | null
  /** True when the 4 deep-dive facets (content_2..5) are locked for this viewer. */
  extra_locked?: boolean
}

/** One of the 4 life peaks ("Đỉnh Cao Cuộc Đời"). */
export interface LifePeak extends NumerologyIndicator {
  stage: number
  age_start: number
}

/** One of the 4 life challenges ("Thử Thách Cuộc Đời"). */
export interface Challenge extends NumerologyIndicator {
  stage: number
}

/** Lo Shu-style digit-frequency maps (keys "1".."9"). */
export interface PowerChart {
  birth: Record<string, number>
  name: Record<string, number>
  /** Birth + name counts merged per digit (G3). */
  combined?: Record<string, number>
}

/** Birth-chart arrows (mũi tên) + isolated corner numbers (G4/G5). */
export interface ChartArrows {
  /** Strength-arrow codes present, e.g. "147". */
  present: string[]
  /** Empty-arrow codes, e.g. "not_123". */
  empty: string[]
  /** Isolated corner numbers (1/3/7/9). */
  isolated: number[]
}

/** The 7 core numbers block (matches GET /api/numerology-report). */
export interface CoreNumbers {
  su_menh: NumerologyIndicator
  linh_hon: NumerologyIndicator
  nhan_cach: NumerologyIndicator
  thai_do: NumerologyIndicator
  truong_thanh: NumerologyIndicator
  ngay_sinh: NumerologyIndicator
  noi_cam: NumerologyIndicator
}

/** Personal-cycle block: personal year (G2) + personal month. */
export interface PersonalCycle {
  nam_ca_nhan?: NumerologyIndicator
  thang_ca_nhan: NumerologyIndicator
}

/** User identity echoed by the report. */
export interface ReportUser {
  name: string
  birth_day_text: string
  age: number
}

/** Full aggregated numerology report payload (the `data` field). */
export interface NumerologyReport {
  user: ReportUser
  so_chu_dao: MainNumberIndicator
  core_numbers: CoreNumbers
  peaks: LifePeak[]
  challenges: Challenge[]
  personal: PersonalCycle
  missing_numbers: NumerologyIndicator[]
  /** Số Nợ Nghiệp — karmic-debt indicators (G1); empty if none. */
  karmic_debt?: NumerologyIndicator[]
  /** Biểu đồ tên — NameChart indicators for digits in the name (G3). */
  name_chart?: NumerologyIndicator[]
  /** Mũi tên + số lẻ loi (G4/G5). */
  arrows?: ChartArrows
  power_chart: PowerChart
}

/** Viewer entitlement tier resolved by the backend. */
export type ReportTier = 'free' | 'paid'

/**
 * GET /api/numerology-report response envelope. Extends the report payload with
 * the resolved entitlement so the UI can drive upsell + PDF flows.
 */
export interface NumerologyReportResponse {
  data: NumerologyReport
  tier: ReportTier
  /** Section keys the viewer may see in full (mirrors backend FREE/ALL sets). */
  unlocked: string[]
  /** The paid order that unlocked this report, when tier === 'paid'. */
  matched_order_id: number | null
  /** UserReport id of the fulfilled PDF for paid viewers (download target). */
  report_download_id: number | null
}
