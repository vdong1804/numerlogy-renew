/**
 * Trang Chính sách bảo mật — SSG, tuân NĐ 13/2023.
 * Placeholders [BRACKETS] để user search & replace.
 */
import { Typography } from '@mui/material'
import type { GetStaticProps } from 'next'

import LegalDocument from '@/components/common/legal-document'
import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

export default function PrivacyPage() {
  return (
    <Main
      meta={
        <Meta
          title="Chính sách bảo mật | Nhân Sinh Quán"
          description="Chính sách bảo mật và xử lý dữ liệu cá nhân tại nhansinhquan.vn theo NĐ 13/2023"
        />
      }
    >
      <PageShell
        title="Chính sách bảo mật"
        subtitle={
          <>
            Cập nhật lần cuối: 26/05/2025 · Phiên bản 1.0
            <br />
            Tuân thủ Nghị định 13/2023/NĐ-CP
          </>
        }
      >
        <LegalDocument>
          <section>
            <h2>1. Giới thiệu</h2>
            <p>
              <strong>[TÊN DOANH NGHIỆP]</strong> (MST: <strong>[MST]</strong>) vận hành
              website <strong>nhansinhquan.vn</strong> cam kết bảo vệ quyền riêng tư của
              bạn. Chính sách này mô tả cách chúng tôi thu thập, sử dụng, lưu trữ và bảo
              vệ dữ liệu cá nhân theo quy định tại Nghị định 13/2023/NĐ-CP về bảo vệ dữ
              liệu cá nhân.
            </p>
          </section>

          <section>
            <h2>2. Dữ liệu chúng tôi thu thập</h2>
            <p>Chúng tôi có thể thu thập các loại dữ liệu sau:</p>
            <table>
              <thead>
                <tr>
                  <th>Loại dữ liệu</th>
                  <th>Chi tiết</th>
                  <th>Bắt buộc</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Email</td>
                  <td>Địa chỉ email đăng ký tài khoản</td>
                  <td>Có</td>
                </tr>
                <tr>
                  <td>Mật khẩu</td>
                  <td>Lưu dạng hash bcrypt, không đọc được</td>
                  <td>Có</td>
                </tr>
                <tr>
                  <td>Số điện thoại</td>
                  <td>Tùy chọn, dùng cho hỗ trợ</td>
                  <td>Không</td>
                </tr>
                <tr>
                  <td>Tên &amp; ngày sinh</td>
                  <td>Dữ liệu đầu vào phân tích số học</td>
                  <td>Có (cho dịch vụ)</td>
                </tr>
                <tr>
                  <td>Địa chỉ IP</td>
                  <td>Tự động ghi nhận khi truy cập</td>
                  <td>Tự động</td>
                </tr>
                <tr>
                  <td>Cookie &amp; log truy cập</td>
                  <td>Session, hành vi điều hướng</td>
                  <td>Tự động</td>
                </tr>
                <tr>
                  <td>Tham chiếu thanh toán</td>
                  <td>Mã giao dịch SePay (không lưu số thẻ)</td>
                  <td>Khi mua hàng</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section>
            <h2>3. Mục đích xử lý dữ liệu</h2>
            <ul>
              <li>Cung cấp dịch vụ phân tích số học và giao hàng báo cáo PDF.</li>
              <li>Xử lý thanh toán qua cổng SePay.</li>
              <li>Gửi email thông báo đơn hàng qua dịch vụ Resend.</li>
              <li>Phân tích hành vi người dùng để cải thiện dịch vụ (chỉ khi có consent).</li>
              <li>Hiển thị quảng cáo phù hợp qua Meta Pixel (chỉ khi có consent marketing).</li>
              <li>Tuân thủ nghĩa vụ pháp lý (kế toán, thuế, phòng chống gian lận).</li>
            </ul>
          </section>

          <section>
            <h2>4. Chia sẻ với bên thứ ba</h2>
            <p>
              Chúng tôi <strong>không bán</strong> dữ liệu cá nhân. Dữ liệu chỉ được chia
              sẻ với:
            </p>
            <ul>
              <li>
                <strong>SePay</strong> — cổng thanh toán, nhận mã tham chiếu giao dịch.
                Xem{' '}
                <a
                  href="https://sepay.vn/chinh-sach-bao-mat.html"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  chính sách SePay
                </a>
                .
              </li>
              <li>
                <strong>Resend</strong> — dịch vụ gửi email giao dịch (email, đơn hàng).
                Xem{' '}
                <a
                  href="https://resend.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  chính sách Resend
                </a>
                .
              </li>
              <li>
                <strong>Google Analytics 4</strong> — phân tích lưu lượng ẩn danh,{' '}
                <em>chỉ khi bạn đồng ý</em>.
              </li>
              <li>
                <strong>Meta Pixel</strong> — tối ưu quảng cáo,{' '}
                <em>chỉ khi bạn đồng ý marketing</em>.
              </li>
              <li>Cơ quan nhà nước theo yêu cầu pháp lý.</li>
            </ul>
          </section>

          <section>
            <h2>5. Thời gian lưu trữ</h2>
            <ul>
              <li>Dữ liệu tài khoản: cho đến khi bạn yêu cầu xóa.</li>
              <li>
                Nhật ký thanh toán: <strong>5 năm</strong> theo Luật Kế toán Việt Nam (Luật
                88/2015/QH13).
              </li>
              <li>Log truy cập: 90 ngày.</li>
              <li>Cookie phân tích (GA4): theo chính sách Google (tối đa 26 tháng).</li>
            </ul>
          </section>

          <section>
            <h2>6. Quyền của bạn (NĐ 13/2023)</h2>
            <p>Theo Nghị định 13/2023/NĐ-CP, bạn có quyền:</p>
            <ul>
              <li>
                <strong>Truy cập:</strong> yêu cầu bản sao dữ liệu cá nhân chúng tôi đang
                lưu.
              </li>
              <li>
                <strong>Chỉnh sửa:</strong> yêu cầu sửa thông tin không chính xác.
              </li>
              <li>
                <strong>Xóa:</strong> yêu cầu xóa tài khoản và dữ liệu liên quan (trừ dữ
                liệu bắt buộc lưu theo luật).
              </li>
              <li>
                <strong>Rút consent:</strong> rút lại sự đồng ý phân tích/marketing bất kỳ
                lúc nào qua banner cookie.
              </li>
              <li>
                <strong>Khiếu nại:</strong> gửi khiếu nại đến Cục An toàn thông tin, Bộ
                TT&amp;TT.
              </li>
            </ul>
            <p>
              Gửi yêu cầu về quyền dữ liệu đến: <strong>[EMAIL DPO / HỖ TRỢ]</strong>.
              Chúng tôi phản hồi trong vòng <strong>72 giờ</strong> làm việc.
            </p>
          </section>

          <section>
            <h2>7. Bảo mật dữ liệu</h2>
            <p>
              Chúng tôi áp dụng các biện pháp kỹ thuật và tổ chức phù hợp: mã hóa HTTPS/TLS,
              mật khẩu hash bcrypt, phân quyền truy cập nội bộ, và giám sát hệ thống 24/7.
              Tuy nhiên, không có hệ thống nào an toàn tuyệt đối. Thông báo vi phạm dữ liệu
              sẽ được gửi theo quy định pháp luật.
            </p>
          </section>

          <section>
            <h2>8. Cookie</h2>
            <p>
              Website sử dụng cookie thiết yếu (session, xác thực) và cookie phân tích/marketing
              (chỉ khi có consent). Bạn có thể quản lý consent qua banner cookie ở cuối trang
              hoặc xóa cookie trong cài đặt trình duyệt.
            </p>
          </section>

          <section>
            <h2>9. Liên hệ về bảo mật dữ liệu</h2>
            <Typography component="p" sx={{ color: 'rgba(255,255,255,0.88)' }}>
              Người phụ trách bảo vệ dữ liệu (DPO): <strong>[TÊN DPO]</strong>
              <br />
              Email: <strong>[EMAIL DPO]</strong>
              <br />
              Địa chỉ: <strong>[ĐỊA CHỈ]</strong>
            </Typography>
          </section>
        </LegalDocument>
      </PageShell>
    </Main>
  )
}

export const getStaticProps: GetStaticProps = async () => ({ props: {} })
