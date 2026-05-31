/**
 * FAQ page — /faq
 * 15 Q&A grouped into 3 sections: Mua hàng, Thanh toán, Báo cáo.
 * Uses native <details> for zero-dep accordion.
 */
import { Box, Typography } from '@mui/material'

import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

interface FaqItem {
  q: string
  a: string
}

interface FaqGroup {
  title: string
  items: FaqItem[]
}

const FAQ_GROUPS: FaqGroup[] = [
  {
    title: 'Mua hàng',
    items: [
      {
        q: 'Làm sao để mua báo cáo thần số học?',
        a: 'Truy cập trang Cửa hàng (/shop), chọn báo cáo hoặc gói phù hợp, nhấn "Mua ngay" và hoàn tất thanh toán. Sau khi thanh toán xác nhận, báo cáo sẽ xuất hiện trong trang "Báo cáo của tôi".',
      },
      {
        q: 'Có những gói sản phẩm nào?',
        a: 'Chúng tôi cung cấp báo cáo lẻ (theo từng chủ đề: tình duyên, sự nghiệp, tài chính…) và các gói combo tiết kiệm hơn so với mua lẻ. Xem chi tiết tại trang Cửa hàng.',
      },
      {
        q: 'Khác biệt giữa báo cáo lẻ và gói combo?',
        a: 'Báo cáo lẻ tập trung vào một chủ đề cụ thể. Gói combo bao gồm nhiều báo cáo với mức giá ưu đãi, phù hợp nếu bạn muốn phân tích toàn diện.',
      },
      {
        q: 'Bao lâu sau khi thanh toán tôi nhận được báo cáo?',
        a: 'Hệ thống tự động xử lý ngay sau khi xác nhận thanh toán, thường trong vòng 1–5 phút. Bạn sẽ nhận email thông báo và có thể tải báo cáo trong mục "Báo cáo của tôi".',
      },
      {
        q: 'Có dùng thử miễn phí không?',
        a: 'Hiện tại chúng tôi chưa có gói dùng thử. Tuy nhiên, trang chủ có công cụ tính số cơ bản miễn phí để bạn trải nghiệm trước.',
      },
    ],
  },
  {
    title: 'Thanh toán',
    items: [
      {
        q: 'Phương thức thanh toán được chấp nhận là gì?',
        a: 'Chúng tôi chấp nhận chuyển khoản ngân hàng nội địa qua mã QR SePay (tự động xác nhận). Hỗ trợ tất cả ngân hàng tại Việt Nam.',
      },
      {
        q: 'Mã nội dung chuyển khoản là gì?',
        a: 'Sau khi đặt hàng, hệ thống sẽ hiển thị mã QR và nội dung chuyển khoản duy nhất cho đơn hàng của bạn. Vui lòng nhập đúng nội dung để hệ thống tự động xác nhận.',
      },
      {
        q: 'Tôi đã thanh toán nhưng chưa nhận được báo cáo, phải làm sao?',
        a: 'Vui lòng đợi 5–10 phút và kiểm tra lại trang "Báo cáo của tôi". Nếu vẫn chưa thấy, liên hệ hỗ trợ qua email admin@nhansinhquan.vn kèm ảnh chụp biên lai chuyển khoản.',
      },
      {
        q: 'Chính sách hoàn tiền như thế nào?',
        a: 'Do báo cáo là sản phẩm số và được giao ngay sau thanh toán, chúng tôi không hoàn tiền sau khi báo cáo đã được tạo. Xem chi tiết tại trang Chính sách hoàn tiền.',
      },
      {
        q: 'Thanh toán có an toàn không?',
        a: 'Có. Chúng tôi không lưu thông tin thẻ hoặc tài khoản ngân hàng của bạn. Toàn bộ giao dịch qua kênh ngân hàng chính thức được mã hóa.',
      },
    ],
  },
  {
    title: 'Báo cáo',
    items: [
      {
        q: 'Báo cáo được gửi ở định dạng nào?',
        a: 'Báo cáo được xuất dưới dạng file PDF, có thể tải về và lưu lâu dài.',
      },
      {
        q: 'Tôi có thể đọc lại báo cáo sau khi tải không?',
        a: 'Có. Báo cáo luôn có sẵn trong mục "Báo cáo của tôi" để tải lại bất cứ lúc nào, miễn là tài khoản của bạn còn hoạt động.',
      },
      {
        q: 'Tôi có thể in báo cáo ra giấy không?',
        a: 'Có. File PDF được thiết kế tương thích với máy in tiêu chuẩn A4.',
      },
      {
        q: 'Báo cáo có hết hạn không?',
        a: 'Báo cáo không có ngày hết hạn. Bạn có thể truy cập và tải lại bất cứ lúc nào trong phạm vi tài khoản còn hoạt động.',
      },
      {
        q: 'Tôi cần hỗ trợ thêm về báo cáo, liên hệ ở đâu?',
        a: 'Gửi email tới admin@nhansinhquan.vn hoặc nhắn tin qua fanpage Facebook của chúng tôi. Chúng tôi phản hồi trong vòng 24 giờ làm việc.',
      },
    ],
  },
]

export default function FaqPage() {
  return (
    <Main
      meta={
        <Meta
          title="Câu hỏi thường gặp | Nhân Sinh Quán"
          description="Giải đáp các thắc mắc về mua hàng, thanh toán và báo cáo thần số học tại nhansinhquan.vn."
        />
      }
    >
      <PageShell
        title="Câu hỏi thường gặp"
        subtitle={
          <>
            Không tìm thấy câu trả lời?{' '}
            <a
              href="/contact"
              style={{
                color: '#F96A2D',
                textDecoration: 'underline',
                textUnderlineOffset: 2,
              }}
            >
              Liên hệ chúng tôi
            </a>
            .
          </>
        }
        bare
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: { xs: 4, md: 5 } }}>
          {FAQ_GROUPS.map((group) => (
            <Box key={group.title}>
              <Typography
                component="h2"
                sx={{
                  fontFamily: 'var(--philosopher-font)',
                  fontWeight: 700,
                  fontSize: { xs: '1.35rem', md: '1.6rem' },
                  mb: 2,
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  '&::before': {
                    content: '""',
                    display: 'inline-block',
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    bgcolor: '#F96A2D',
                    boxShadow: '0 0 12px rgba(249,106,45,0.6)',
                  },
                }}
              >
                {group.title}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {group.items.map((item) => (
                  <Box
                    key={item.q}
                    component="details"
                    sx={{
                      borderRadius: 3,
                      border: '1px solid rgba(255,255,255,0.10)',
                      bgcolor: 'rgba(255,255,255,0.04)',
                      backdropFilter: 'blur(8px)',
                      px: { xs: 2, md: 2.5 },
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        borderColor: 'rgba(249,106,45,0.45)',
                        bgcolor: 'rgba(255,255,255,0.06)',
                      },
                      '&[open]': {
                        pb: 2,
                        borderColor: 'rgba(249,106,45,0.55)',
                        bgcolor: 'rgba(255,255,255,0.07)',
                      },
                      '&[open] summary::after': { transform: 'rotate(45deg)' },
                    }}
                  >
                    <Box
                      component="summary"
                      sx={{
                        py: 2,
                        fontWeight: 600,
                        fontSize: '0.98rem',
                        cursor: 'pointer',
                        userSelect: 'none',
                        listStyle: 'none',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 2,
                        color: '#fff',
                        '&::-webkit-details-marker': { display: 'none' },
                        '&::after': {
                          content: '"+"',
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 24,
                          height: 24,
                          fontSize: '1.3rem',
                          color: '#F96A2D',
                          transition: 'transform 0.2s ease',
                          flexShrink: 0,
                        },
                      }}
                    >
                      {item.q}
                    </Box>
                    <Typography
                      sx={{
                        color: 'rgba(255,255,255,0.78)',
                        lineHeight: 1.75,
                        fontSize: '0.92rem',
                      }}
                    >
                      {item.a}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          ))}
        </Box>
      </PageShell>
    </Main>
  )
}
