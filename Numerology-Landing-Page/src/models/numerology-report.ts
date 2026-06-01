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
}

/** Hero "Số Chủ Đạo" indicator: may carry extra content blocks 2..5. */
export interface MainNumberIndicator extends NumerologyIndicator {
  content_2?: string | null
  content_3?: string | null
  content_4?: string | null
  content_5?: string | null
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
}

/** The 9 core numbers block. */
export interface CoreNumbers {
  su_menh: NumerologyIndicator
  linh_hon: NumerologyIndicator
  nhan_cach: NumerologyIndicator
  thai_do: NumerologyIndicator
  truong_thanh: NumerologyIndicator
  ngay_sinh: NumerologyIndicator
  can_bang: NumerologyIndicator
  thuc_thi: NumerologyIndicator
  noi_cam: NumerologyIndicator
}

/** Personal year/month cycle block. */
export interface PersonalCycle {
  nam_ca_nhan: NumerologyIndicator
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
  power_chart: PowerChart
}
