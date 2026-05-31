/**
 * Hướng dẫn sử dụng — /huong-dan
 * 5-step visual guide: đăng ký → mua → checkout → email → xem báo cáo.
 */
import { Box, Button, Typography } from '@mui/material'

import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

interface GuideStep {
  number: number
  title: string
  description: string
}

const STEPS: GuideStep[] = [
  {
    number: 1,
    title: 'Đăng ký tài khoản miễn phí',
    description:
      'Truy cập trang Đăng ký, điền họ tên và email, tạo mật khẩu. Tài khoản được kích hoạt ngay lập tức — không cần xác nhận email.',
  },
  {
    number: 2,
    title: 'Chọn báo cáo trong Cửa hàng',
    description:
      'Vào trang Cửa hàng, duyệt qua các báo cáo theo chủ đề (tình duyên, sự nghiệp, tài chính, sức khỏe…) hoặc chọn gói combo tiết kiệm. Nhấn "Mua ngay" để thêm vào đơn hàng.',
  },
  {
    number: 3,
    title: 'Thanh toán qua mã QR SePay',
    description:
      'Hệ thống hiển thị mã QR và số tiền cần chuyển. Mở ứng dụng ngân hàng, quét mã QR, nhập đúng nội dung chuyển khoản và xác nhận. Thanh toán được xác nhận tự động trong vòng 1–5 phút.',
  },
  {
    number: 4,
    title: 'Nhận email xác nhận',
    description:
      'Sau khi thanh toán thành công, chúng tôi gửi email xác nhận đơn hàng kèm thông báo báo cáo đã sẵn sàng. Kiểm tra hộp thư đến (và thư mục Spam nếu không thấy).',
  },
  {
    number: 5,
    title: 'Xem và tải báo cáo',
    description:
      'Đăng nhập và vào trang "Báo cáo của tôi" (/my-account/reports). Báo cáo PDF xuất hiện tại đây — nhấn "Tải PDF" để lưu về máy. Bạn có thể tải lại bất cứ lúc nào.',
  },
]

export default function HuongDanPage() {
  return (
    <Main
      meta={
        <Meta
          title="Hướng dẫn sử dụng | Nhân Sinh Quán"
          description="Hướng dẫn từng bước cách đăng ký, mua và nhận báo cáo thần số học tại nhansinhquan.vn."
        />
      }
    >
      <PageShell
        title="Hướng dẫn sử dụng"
        subtitle="Chỉ 5 bước đơn giản để khám phá thần số học của bạn."
        bare
      >
        <Box
          sx={{
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            gap: { xs: 2.5, md: 3 },
          }}
        >
          {/* Vertical connecting line (desktop) */}
          <Box
            sx={{
              display: { xs: 'none', md: 'block' },
              position: 'absolute',
              left: 28,
              top: 28,
              bottom: 28,
              width: 2,
              bgcolor: 'rgba(249,106,45,0.25)',
              zIndex: 0,
            }}
          />

          {STEPS.map((step) => (
            <Box
              key={step.number}
              sx={{
                position: 'relative',
                zIndex: 1,
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: { xs: 2, sm: 3 },
                alignItems: { xs: 'flex-start', sm: 'stretch' },
                p: { xs: 2.5, md: 3 },
                borderRadius: 3,
                bgcolor: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.10)',
                backdropFilter: 'blur(10px)',
                transition: 'all 0.25s ease',
                '&:hover': {
                  borderColor: 'rgba(249,106,45,0.45)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 12px 30px -12px rgba(0,0,0,0.4)',
                },
              }}
            >
              {/* Step number badge */}
              <Box
                sx={{
                  flexShrink: 0,
                  width: 56,
                  height: 56,
                  borderRadius: '50%',
                  background:
                    'linear-gradient(135deg, #F96A2D 0%, #FF8F5E 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 8px 20px -6px rgba(249,106,45,0.55)',
                }}
              >
                <Typography
                  component="span"
                  sx={{
                    fontFamily: 'var(--philosopher-font)',
                    fontWeight: 700,
                    fontSize: '1.7rem',
                    color: '#fff',
                    lineHeight: 1,
                  }}
                >
                  {step.number}
                </Typography>
              </Box>

              {/* Text content */}
              <Box sx={{ flex: 1 }}>
                <Typography
                  component="h3"
                  sx={{
                    fontFamily: 'var(--philosopher-font)',
                    fontWeight: 700,
                    fontSize: { xs: '1.1rem', md: '1.25rem' },
                    color: '#fff',
                    mb: 0.75,
                  }}
                >
                  {step.title}
                </Typography>
                <Typography
                  sx={{
                    color: 'rgba(255,255,255,0.78)',
                    lineHeight: 1.75,
                    fontSize: '0.93rem',
                  }}
                >
                  {step.description}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>

        {/* CTA */}
        <Box
          sx={{
            mt: { xs: 6, md: 8 },
            textAlign: 'center',
            p: { xs: 3, md: 5 },
            borderRadius: 4,
            background:
              'linear-gradient(135deg, rgba(249,106,45,0.14) 0%, rgba(111,73,253,0.14) 100%)',
            border: '1px solid rgba(249,106,45,0.30)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Typography
            component="h3"
            sx={{
              fontFamily: 'var(--philosopher-font)',
              fontWeight: 700,
              fontSize: { xs: '1.4rem', md: '1.75rem' },
              color: '#fff',
              mb: 1,
            }}
          >
            Sẵn sàng bắt đầu hành trình?
          </Typography>
          <Typography
            sx={{
              color: 'rgba(255,255,255,0.78)',
              mb: 3,
              fontSize: '0.95rem',
            }}
          >
            Tạo tài khoản miễn phí và khám phá thần số học ngay hôm nay.
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 2,
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <Button
              component="a"
              href="/register"
              variant="contained"
              color="primary"
              size="large"
            >
              Đăng ký miễn phí
            </Button>
            <Button
              component="a"
              href="/shop"
              variant="outlined"
              size="large"
              sx={{
                color: '#fff',
                borderColor: 'rgba(255,255,255,0.35)',
                '&:hover': {
                  borderColor: '#fff',
                  bgcolor: 'rgba(255,255,255,0.08)',
                },
              }}
            >
              Xem Cửa hàng
            </Button>
          </Box>
        </Box>
      </PageShell>
    </Main>
  )
}
