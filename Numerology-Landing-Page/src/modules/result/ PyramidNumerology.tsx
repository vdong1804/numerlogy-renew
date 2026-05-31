import { Box, Typography } from '@mui/material'

import { AlertWarning } from '@/components/alert'
import { IconEyeOff } from '@/components/icon'

import { BoxContentDetail } from './parts'

export interface PyramidNumerologyProps {
  isVip: boolean
}

export default function PyramidNumerology({
  isVip = false,
}: PyramidNumerologyProps) {
  return (
    <BoxContentDetail title="5. KIM TỰ THÁP THẦN SỐ HỌC">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Typography fontStyle={'italic'}>
          Kim tự tháp cho thấy 4 giai đoạn trong cuộc đời bạn sẽ tương ứng với
          đỉnh cao là số nào và thử thách là con số nào, tức là bạn nên tập
          trung phát triển số nào trong những năm này để đạt được nhiều thành
          công và hạnh phúc nhất. Từ tuổi đỉnh cao đầu tiên đến tuổi đỉnh cao
          cuối cùng (36 năm) chính là khoảng thời gian gặt hái nhiều thành công
          trong cuộc đời của bạn. Tuy vậy, trong 4 giai đoạn này cũng sẽ có
          những thách thức cụ thể mà cuộc đời muốn bạn vượt qua - những con số
          thử thách sẽ nói lên điều đó.
        </Typography>
        <Box
          component={'img'}
          src="https://thanglongdaoquan.vn/wp-content/uploads/kim-tu-thap-5.jpg"
          sx={{
            width: {
              xs: '100%',
              md: '75%',
            },
            borderRadius: '10px',
            margin: '0 auto',
          }}
        />

        <Box>
          <Box display={'flex'} alignItems={'center'}>
            <Typography
              component={'h4'}
              mr={1.25}
              className="text-heading-secondary"
            >
              5.1. GIAI ĐOẠN TỪ ĐẦU ĐỜI TỚI NĂM 27 TUỔI (2021), BẠN CÓ ĐỈNH CAO
              LÀ SỐ 4 VÀ THỬ THÁCH LÀ SỐ
            </Typography>
            <IconEyeOff />
          </Box>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Mục này cho biết hướng bạn nên phát triển trong giai đoạn từ đầu
                đời tới năm 27 tuổi này để đạt đỉnh cao và những tiêu cực cần
                khắc phục. Bạn cần nâng cấp Vip để xem được luận giải của mục
                này.
              </AlertWarning>
            )}
          </Box>
        </Box>

        <Box>
          <Box display={'flex'} alignItems={'center'}>
            <Typography
              component={'h4'}
              mr={1.25}
              className="text-heading-secondary"
            >
              5.2. GIAI ĐOẠN HAI TỪ NĂM 28 TUỔI (2022) TỚI 36 TUỔI (2030), BẠN
              CÓ ĐỈNH CAO LÀ SỐ 8 VÀ THỬ THÁCH LÀ SỐ
            </Typography>
            <IconEyeOff />
          </Box>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Mục này cho biết hướng bạn nên phát triển trong giai đoạn nói
                trên để đạt đỉnh cao và những tiêu cực cần khắc phục. Bạn cần
                nâng cấp Vip để xem được luận giải của mục này.
              </AlertWarning>
            )}
          </Box>
        </Box>

        <Box>
          <Box display={'flex'} alignItems={'center'}>
            <Typography
              component={'h4'}
              mr={1.25}
              className="text-heading-secondary"
            >
              5.3. GIAI ĐOẠN BA TỪ NĂM 37 TUỔI (2031) TỚI 45 TUỔI (2039), BẠN CÓ
              ĐỈNH CAO LÀ SỐ 3 VÀ THỬ THÁCH LÀ SỐ
            </Typography>
            <IconEyeOff />
          </Box>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Mục này cho biết hướng bạn nên phát triển trong giai đoạn này để
                đạt đỉnh cao và những tiêu cực cần khắc phục. Bạn cần nâng cấp
                Vip để xem được luận giải của mục này.
              </AlertWarning>
            )}
          </Box>
        </Box>

        <Box>
          <Box display={'flex'} alignItems={'center'}>
            <Typography
              component={'h4'}
              mr={1.25}
              className="text-heading-secondary"
            >
              5.4. GIAI ĐOẠN TỪ NĂM 46 TUỔI (2040) TỚI CUỐI ĐỜI, BẠN CÓ ĐỈNH CAO
              LÀ SỐ 6 VÀ THỬ THÁCH LÀ SỐ
            </Typography>
            <IconEyeOff />
          </Box>
          <Box mt={1.25}>
            {isVip ? (
              <>aaaa</>
            ) : (
              <AlertWarning>
                Mục này cho biết hướng bạn nên phát triển trong giai đoạn nói
                trên để đạt đỉnh cao và những tiêu cực cần khắc phục. Bạn cần
                nâng cấp Vip để xem được luận giải của mục này.
              </AlertWarning>
            )}
          </Box>
        </Box>
      </Box>
    </BoxContentDetail>
  )
}
