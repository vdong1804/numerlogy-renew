/**
 * Registry of all numerology content resource slugs with Vietnamese labels
 * Used by admin sidebar nav and content CRUD pages
 */

export interface ContentResource {
  slug: string
  label: string
  /** Whether this resource has content_2..5 extra fields (main-number only) */
  hasExtraContent?: boolean
  /** Whether this resource uses only code + bow fields (phone-master-data) */
  isPhoneMaster?: boolean
}

export const CONTENT_RESOURCES: ContentResource[] = [
  { slug: 'main-number', label: 'Số Chủ Đạo', hasExtraContent: true },
  { slug: 'mission-number', label: 'Số Sứ Mệnh' },
  { slug: 'souls-number', label: 'Số Linh Hồn' },
  { slug: 'development-number', label: 'Số Trưởng Thành' },
  { slug: 'growth-number', label: 'Số Phát Triển' },
  { slug: 'life-peak', label: 'Đỉnh Cao Cuộc Đời' },
  { slug: 'challenge-life', label: 'Thách Thức Cuộc Đời' },
  { slug: 'birthday-chart', label: 'Biểu Đồ Ngày Sinh' },
  { slug: 'name-chart', label: 'Biểu Đồ Tên' },
  { slug: 'stages-of-life', label: 'Các Giai Đoạn Cuộc Đời' },
  { slug: 'attitude-number', label: 'Số Thái Độ' },
  { slug: 'birthday-number', label: 'Số Ngày Sinh' },
  { slug: 'mature-number', label: 'Số Nhân Cách' },
  { slug: 'introspective-number', label: 'Số Nội Tâm' },
  { slug: 'karmic-number', label: 'Số Nghiệp' },
  { slug: 'phone-number', label: 'Số Điện Thoại' },
  { slug: 'personal-month-number', label: 'Số Tháng Cá Nhân' },
  { slug: 'identifiable', label: 'Số Nhận Diện' },
  { slug: 'miss-number', label: 'Số Bỏ Lỡ' },
  { slug: 'personal-year-number', label: 'Số Năm Cá Nhân' },
]

export function findResource(slug: string): ContentResource | undefined {
  return CONTENT_RESOURCES.find((r) => r.slug === slug)
}

export const CONTENT_RESOURCE_SLUGS = CONTENT_RESOURCES.map((r) => r.slug)
