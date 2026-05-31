import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

export interface LifeNumberProps {
  isVip: boolean
}
const TitlePage = () => (
  <>
    3. CHỈ SỐ ĐƯỜNG ĐỜI (SỐ CHỦ ĐẠO) CỦA BẠN LÀ:{' '}
    <Typography component={'span'} className="text-heading" color={'#41DA63'}>
      SỐ 9 – TRÁCH NHIỆM VÀ LÝ TƯỞNG
    </Typography>
  </>
)

export default function LifeNumber({ isVip = false }: LifeNumberProps) {
  return (
    <BoxContentDetail title={<TitlePage />}>
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Typography fontStyle={'italic'}>
          Chỉ số này hé lộ con đường mà bạn sẽ trải qua trong cuộc đời này. Nó
          cho bạn thấy bạn sẽ gặp phải những trải nghiệm như thế nào, và bạn học
          được gì sau những trải nghiệm đó. Nó cung cấp nhiều thông tin về con
          người bạn và cuộc đời mà bạn sẽ sống.
        </Typography>
        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            ĐIỂM MẠNH CỦA BẠN:
          </Typography>
          <Box mt={1.25}>
            <Typography>
              - Bạn là một nhà lãnh đạo bẩm sinh. Điểm đặc biệt nhất ở bạn là
              tạo dựng được lòng tin từ người khác một cách tự nhiên. Khi tiếp
              xúc với bạn, nhất là nếu bạn có tư duy tích cực, bạn sẽ cực kỳ tỏa
              sáng. Điều đó có thể làm cho mọi người chú ý đến bạn, tin tưởng
              bạn hoặc thậm chí là đi theo bạn.
            </Typography>
            <Typography>
              - Bạn cũng là người có tinh thần nhân đạo cao độ. Bạn thường nghĩ
              cho người khác, cho công chúng và cho cộng đồng lớn. Bạn nghĩ cho
              nhân loại. Bạn có thể thấu hiểu được nỗi đau, khó khăn của những
              người nghèo khó, khuyết tật, neo đơn, những người yếu thế. Bạn
              thường có xu hướng giúp đỡ mọi người, cộng đồng.
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            ĐIỂM YẾU CỦA BẠN
          </Typography>
          <Box mt={1.25}>
            <Typography>
              - Bạn có thể dễ bị những vấn đề tiêu cực trong quá khứ đeo bám và
              ảnh hưởng. Nếu có những vấn đề như vậy, bạn hãy bước qua bằng cách
              tập trung vào hiện tại, làm cho tốt. Bạn cũng nên tập những môn
              vận động, tập thiền, yoga để thư giãn tinh thần và nâng cao trí
              tuệ. Bước qua quá khứ và có tinh thần tích cực sẽ giúp bạn tạo ra
              sự thay đổi lớn đối với thế giới xung quanh.
            </Typography>
            <Typography>
              - Vì bạn khá hào phóng nên bạn có thể thấy rằng tài chính của bạn
              không ở trong tình trạng tốt nhất. Bạn dễ mang tiền tặng cho những
              người cần đến, hơn là ý thức tiết kiệm để dành lại cho chính mình,
              và điều này cũng dễ làm cho người thân (đặc biệt là bạn đời) của
              bạn nổi giận.
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            NHỮNG NGƯỜI NỔI TIẾNG CÓ SỐ 9
          </Typography>
          <Box mt={1.25}>
            <Typography>- Đại Tướng Võ Nguyên Giáp</Typography>
            <Typography>- Phan Thị Bích Hằng – Nhà ngoại cảm</Typography>
            <Typography mt={2.5}>
              Vì bạn khá hào phóng nên bạn có thể thấy rằng tài chính của bạn
              không ở trong tình trạng tốt nhất. Bạn dễ mang tiền tặng cho những
              người cần đến, hơn là ý thức tiết kiệm để dành lại cho chính mình,
              và điều này cũng dễ làm cho người thân (đặc biệt là bạn đời) của
              bạn nổi giận.
            </Typography>
          </Box>
        </Box>

        <Typography component={'h4'} className="text-heading-secondary">
          Mối quan hệ tương thích
        </Typography>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            MỐI QUAN HỆ NÓI CHUNG TRONG CUỘC SỐNG
          </Typography>
          <Box mt={1.25}>
            <Typography>
              Những số đường đời tương thích nhất với bạn:
            </Typography>
            <Typography>
              Số 10: Đường đời số 9 và số 10 là hai cực đối lập nhau - cả về số
              học và tính cách. Sự kết hợp này có thể không hiệu quả trong kinh
              doanh, nhưng thành ngữ đối lập thu hút có thể đúng khi nói về mối
              quan hệ cá nhân của cả hai.
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            TÌNH DUYÊN
          </Typography>
          <Box mt={1.25}>
            <Typography>
              - Tình yêu lớn nhất của bạn là ước mơ của mình. Theo đuổi sự nhân
              đạo có thể quan trọng đối với bạn hơn mối quan hệ cá nhân với
              người khác. Điều này có thể khiến chuyện tình cảm trở nên rắc rối
              hơn đối bạn. Nhưng nếu người bạn đời thực sự hiểu bạn, điều đó có
              thể tạo nên một mối quan hệ thực sự viên mãn.
            </Typography>
            <Typography>
              - Trong khi bạn dễ dàng thu hút người khác, bạn đôi khi có thể tỏ
              ra xa cách khi nói đến các mối quan hệ thân thiết. Rốt cuộc, những
              cảm xúc tự nhiên nảy sinh trong các mối quan hệ thân thiết lại rất
              phù hợp với bạn. Điều đó nói rằng, nếu được chọn đúng bạn đời, bạn
              rất lãng mạn, và thậm chí là ngây thơ trong tình yêu. Một mặt, bạn
              sẽ thường đòi hỏi nhiều tự do để theo đuổi những sở thích bên
              ngoài mối quan hệ và rất khó thay đổi điều đó. Mặt khác, bạn có
              thể có xu hướng giải cứu bạn đời của mình và trong quá trình này,
              bạn phải hy sinh bản thân
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            Bài học và các mặt khác trong cuộc sống
          </Typography>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Chỉ tài khoản Vip mới xem được mục này!
              </AlertWarning>
            )}
          </Box>
        </Box>

        <Box>
          <Typography component={'h4'} className="text-heading-secondary">
            Nghề nghiệp phù hợp
          </Typography>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Chỉ tài khoản Vip mới xem được mục này!
              </AlertWarning>
            )}
          </Box>
        </Box>
      </Box>
    </BoxContentDetail>
  )
}
