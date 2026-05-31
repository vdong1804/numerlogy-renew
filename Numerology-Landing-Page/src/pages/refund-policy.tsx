/**
 * Trang Chính sách hoàn tiền — SSG, tiếng Việt.
 * Placeholders [BRACKETS] để user search & replace.
 */
import { Box } from '@mui/material'
import type { GetStaticProps } from 'next'

import LegalDocument from '@/components/common/legal-document'
import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

export default function RefundPolicyPage() {
  return (
    <Main
      meta={
        <Meta
          title="Chính sách hoàn tiền | Nhân Sinh Quán"
          description="Chính sách hoàn tiền và đổi trả cho dịch vụ phân tích số học tại nhansinhquan.vn"
        />
      }
    >
      <PageShell
        title="Chính sách hoàn tiền"
        subtitle="Cập nhật lần cuối: 26/05/2025 · Phiên bản 1.0"
      >
        <LegalDocument>
          <section>
            <h2>1. Cam kết hoàn tiền</h2>
            <p>
              Chúng tôi muốn bạn hoàn toàn hài lòng với dịch vụ. Nếu vì bất kỳ lý do gì
              bạn không hài lòng, chúng tôi sẵn sàng xem xét hoàn tiền theo các điều kiện
              dưới đây.
            </p>
          </section>

          <section>
            <h2>2. Điều kiện hoàn tiền 100%</h2>
            <p>
              Bạn được hoàn <strong>100% số tiền đã thanh toán</strong> nếu đáp ứng đồng
              thời:
            </p>
            <ul>
              <li>
                Yêu cầu trong vòng <strong>7 ngày</strong> kể từ ngày thanh toán thành
                công.
              </li>
              <li>
                Báo cáo số học PDF <strong>chưa được tạo ra</strong> (chưa render). Sau khi
                hệ thống đã render và giao báo cáo PDF, đơn hàng được coi là đã hoàn thành
                vì đây là sản phẩm số không thể thu hồi.
              </li>
            </ul>
            <Box
              sx={{
                mt: 1.5,
                p: 2,
                borderRadius: 2,
                bgcolor: 'rgba(235,87,87,0.10)',
                border: '1px solid rgba(235,87,87,0.30)',
                color: '#FCA5A5',
                fontSize: '0.92rem',
                lineHeight: 1.65,
              }}
            >
              <strong style={{ color: '#FECACA' }}>Lưu ý quan trọng:</strong> Sau khi báo
              cáo PDF đã được tạo và giao cho bạn, chúng tôi{' '}
              <strong style={{ color: '#FECACA' }}>không thể hoàn tiền</strong> vì sản
              phẩm số đã được sử dụng. Điều này phù hợp với quy định về hàng hóa kỹ thuật
              số theo Luật Bảo vệ quyền lợi người tiêu dùng Việt Nam.
            </Box>
          </section>

          <section>
            <h2>3. Các trường hợp không được hoàn tiền</h2>
            <ul>
              <li>Báo cáo PDF đã được render và giao thành công.</li>
              <li>Yêu cầu hoàn tiền sau 7 ngày kể từ ngày thanh toán.</li>
              <li>
                Thông tin đầu vào (tên, ngày sinh) cung cấp sai — vui lòng kiểm tra kỹ
                trước khi thanh toán.
              </li>
              <li>Vi phạm Điều khoản sử dụng dẫn đến đình chỉ tài khoản.</li>
            </ul>
          </section>

          <section>
            <h2>4. Quy trình yêu cầu hoàn tiền</h2>
            <ol>
              <li>
                Liên hệ bộ phận hỗ trợ qua email <strong>[EMAIL HỖ TRỢ]</strong> hoặc{' '}
                <a href="/contact">trang Liên hệ</a> với tiêu đề:{' '}
                <em>&ldquo;Yêu cầu hoàn tiền — Mã đơn [MÃ ĐƠN HÀNG]&rdquo;</em>.
              </li>
              <li>
                Cung cấp: địa chỉ email đăng ký, mã đơn hàng (ref code) và lý do yêu cầu.
              </li>
              <li>
                Đội ngũ xem xét và phản hồi trong vòng{' '}
                <strong>1–3 ngày làm việc</strong>.
              </li>
              <li>
                Nếu yêu cầu được chấp thuận, tiền hoàn qua cổng SePay về tài khoản ngân
                hàng gốc trong vòng <strong>3–5 ngày làm việc</strong> (tùy ngân hàng).
              </li>
            </ol>
          </section>

          <section>
            <h2>5. Lỗi kỹ thuật từ phía chúng tôi</h2>
            <p>
              Nếu thanh toán thành công nhưng hệ thống không giao báo cáo do lỗi kỹ thuật
              từ phía chúng tôi, bạn sẽ được ưu tiên xử lý ngay: hoàn tiền{' '}
              <strong>100%</strong> hoặc render lại báo cáo miễn phí theo lựa chọn của
              bạn.
            </p>
          </section>

          <section>
            <h2>6. Liên hệ hỗ trợ</h2>
            <p>
              Email: <strong>[EMAIL HỖ TRỢ]</strong>
              <br />
              Zalo OA: <strong>[ZALO OA LINK]</strong>
              <br />
              Giờ làm việc: Thứ 2 – Thứ 6, 8:00 – 17:30 (GMT+7)
            </p>
          </section>
        </LegalDocument>
      </PageShell>
    </Main>
  )
}

export const getStaticProps: GetStaticProps = async () => ({ props: {} })
