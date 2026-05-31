/**
 * Trang Điều khoản sử dụng — SSG, tiếng Việt.
 * Placeholders [BRACKETS] để user search & replace.
 */
import type { GetStaticProps } from 'next'

import LegalDocument from '@/components/common/legal-document'
import PageShell from '@/components/common/page-shell'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'

export default function TermsPage() {
  return (
    <Main
      meta={
        <Meta
          title="Điều khoản sử dụng | Nhân Sinh Quán"
          description="Điều khoản sử dụng dịch vụ phân tích số học nhân sinh tại nhansinhquan.vn"
        />
      }
    >
      <PageShell
        title="Điều khoản sử dụng"
        subtitle="Cập nhật lần cuối: 26/05/2025 · Phiên bản 1.0"
      >
        <LegalDocument>
          <section>
            <h2>1. Chấp nhận điều khoản</h2>
            <p>
              Bằng cách truy cập hoặc sử dụng website <strong>nhansinhquan.vn</strong> và
              các dịch vụ liên quan (gọi chung là &ldquo;Dịch vụ&rdquo;), bạn xác nhận đã
              đọc, hiểu và đồng ý bị ràng buộc bởi các Điều khoản sử dụng này. Nếu bạn
              không đồng ý với bất kỳ điều khoản nào, vui lòng ngừng sử dụng Dịch vụ ngay
              lập tức.
            </p>
            <p>
              Dịch vụ được cung cấp bởi <strong>[TÊN DOANH NGHIỆP]</strong>, mã số thuế{' '}
              <strong>[MST]</strong>, địa chỉ <strong>[ĐỊA CHỈ ĐẦY ĐỦ]</strong> (sau đây
              gọi là &ldquo;Chúng tôi&rdquo;).
            </p>
          </section>

          <section>
            <h2>2. Điều kiện sử dụng</h2>
            <p>Bạn phải đáp ứng các điều kiện sau để sử dụng Dịch vụ:</p>
            <ul>
              <li>
                Từ đủ <strong>18 tuổi</strong> trở lên hoặc có sự đồng ý của người giám hộ
                hợp pháp.
              </li>
              <li>
                Không sử dụng Dịch vụ cho bất kỳ mục đích phi pháp hoặc trái với các quy
                định tại Điều khoản này.
              </li>
              <li>Cung cấp thông tin chính xác, đầy đủ khi đăng ký tài khoản.</li>
            </ul>
          </section>

          <section>
            <h2>3. Tài khoản người dùng</h2>
            <p>
              Bạn chịu trách nhiệm bảo mật thông tin đăng nhập và mọi hoạt động xảy ra
              dưới tài khoản của bạn. Thông báo ngay cho chúng tôi nếu phát hiện truy cập
              trái phép qua email <strong>[EMAIL HỖ TRỢ]</strong>. Chúng tôi có quyền tạm
              khóa hoặc chấm dứt tài khoản vi phạm Điều khoản mà không cần thông báo
              trước.
            </p>
          </section>

          <section>
            <h2>4. Thanh toán và đơn hàng</h2>
            <p>
              Tất cả giá hiển thị trên website là giá cuối (đã bao gồm thuế nếu có), đơn
              vị VNĐ. Chúng tôi chấp nhận thanh toán qua cổng SePay (chuyển khoản ngân
              hàng, QR VietQR). Đơn hàng được xem là hoàn tất sau khi hệ thống xác nhận
              thanh toán thành công. Chính sách hoàn tiền áp dụng theo{' '}
              <a href="/refund-policy">Chính sách hoàn tiền</a>.
            </p>
          </section>

          <section>
            <h2>5. Quyền sở hữu trí tuệ</h2>
            <p>
              Toàn bộ nội dung trên website bao gồm văn bản, hình ảnh, logo, giao diện,
              báo cáo số học được tạo ra thuộc quyền sở hữu của Chúng tôi hoặc các đơn vị
              cấp phép. Bạn được cấp phép sử dụng cá nhân, phi thương mại. Nghiêm cấm sao
              chép, phân phối, bán lại nội dung dưới bất kỳ hình thức nào khi chưa có sự
              chấp thuận bằng văn bản.
            </p>
          </section>

          <section>
            <h2>6. Hành vi bị cấm</h2>
            <p>Người dùng không được:</p>
            <ul>
              <li>Sử dụng bot, scraper hoặc công cụ tự động để thu thập dữ liệu.</li>
              <li>Cố tình làm hỏng hoặc gián đoạn hệ thống.</li>
              <li>Mạo danh người khác hoặc cung cấp thông tin sai lệch.</li>
              <li>Sử dụng Dịch vụ để phát tán spam, lừa đảo hoặc vi phạm pháp luật.</li>
              <li>
                Chia sẻ tài khoản hoặc báo cáo được tạo ra cho bên thứ ba vì mục đích
                thương mại.
              </li>
            </ul>
          </section>

          <section>
            <h2>7. Giới hạn trách nhiệm</h2>
            <p>
              Dịch vụ phân tích số học được cung cấp &ldquo;nguyên trạng&rdquo; mang tính
              tham khảo. Chúng tôi không đảm bảo tính chính xác tuyệt đối hay kết quả cụ
              thể từ việc áp dụng thông tin số học. Trong mọi trường hợp, trách nhiệm của
              Chúng tôi không vượt quá số tiền bạn đã thanh toán cho Dịch vụ liên quan.
            </p>
          </section>

          <section>
            <h2>8. Sửa đổi điều khoản</h2>
            <p>
              Chúng tôi có quyền cập nhật Điều khoản này bất kỳ lúc nào. Thay đổi có hiệu
              lực ngay khi đăng tải. Tiếp tục sử dụng Dịch vụ sau thời điểm cập nhật đồng
              nghĩa với việc bạn chấp nhận Điều khoản mới.
            </p>
          </section>

          <section>
            <h2>9. Luật áp dụng và giải quyết tranh chấp</h2>
            <p>
              Điều khoản này được điều chỉnh theo pháp luật nước Cộng hòa Xã hội Chủ nghĩa
              Việt Nam. Mọi tranh chấp phát sinh sẽ được ưu tiên giải quyết thông qua
              thương lượng. Trường hợp không đạt được thỏa thuận, tranh chấp sẽ được đưa
              ra Tòa án nhân dân có thẩm quyền tại <strong>TP. Hồ Chí Minh</strong>.
            </p>
          </section>

          <section>
            <h2>10. Liên hệ</h2>
            <p>
              Mọi thắc mắc về Điều khoản, vui lòng liên hệ:{' '}
              <a href="/contact">trang Liên hệ</a> hoặc email{' '}
              <strong>[EMAIL HỖ TRỢ]</strong>.
            </p>
          </section>
        </LegalDocument>
      </PageShell>
    </Main>
  )
}

export const getStaticProps: GetStaticProps = async () => ({ props: {} })
