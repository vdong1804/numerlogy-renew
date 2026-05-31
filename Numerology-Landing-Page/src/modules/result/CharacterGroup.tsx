import {
  Box,
  LinearProgress,
  linearProgressClasses,
  styled,
  Typography,
} from '@mui/material'
import * as React from 'react'

import { AlertWarning } from '@/components/alert'

import { BoxContentDetail } from './parts'

const CustomProgress = styled(LinearProgress)(() => ({
  height: 12,
  borderRadius: 20,
  [`&.${linearProgressClasses.colorPrimary}`]: {
    backgroundColor: 'rgba(221, 228, 238, 0.1)',
  },
  [`& .${linearProgressClasses.bar}`]: {
    borderRadius: 5,
    backgroundColor: '#0560FD',
  },
}))

export interface ICharacterGroupProps {
  isVip?: boolean
}

export default function CharacterGroup({
  isVip = false,
}: ICharacterGroupProps) {
  return (
    <BoxContentDetail title="2. NHÓM TÍNH CÁCH THEO BẢN NGÃ CỦA BẠN (có thể thay đổi do luyện tập)">
      <Box sx={{ display: 'flex', flexDirection: 'column', rowGap: 2.5 }}>
        <Typography>
          Đây là các nhóm tính cách có trong bản ngã (tính cách khi sinh ra đã
          có) của bạn. Bạn nên tập trung luyện tập những nhóm tính cách có % dao
          động thấp nhất. Dao động tính cách đẹp nhất khi các chỉ số % gần bằng
          nhau. Bạn hoàn toàn có thể luyện tập để cân bằng và kiểm soát các dao
          động tính cách của bạn.
        </Typography>
        <Box>
          <Typography className="text-heading-secondary" component={'h4'}>
            1.1. Mạnh mẽ - Độc lập - Tự tin
          </Typography>
          <Box mt={2.5} ml={1} display={'flex'} alignItems={'center'}>
            <Typography
              component={'span'}
              width={40}
              fontSize={12}
              fontWeight={500}
              flexShrink={0}
            >
              30%
            </Typography>
            <Box flexGrow={1}>
              <CustomProgress value={30} variant="determinate" />
            </Box>
          </Box>
        </Box>

        <Box>
          <Typography className="text-heading-secondary" component={'h4'}>
            1.2. Lắng nghe - Khéo léo - Nhạy cảm
          </Typography>
          <Box mt={2.5} ml={1} display={'flex'} alignItems={'center'}>
            <Typography
              component={'span'}
              width={40}
              fontSize={12}
              fontWeight={500}
              flexShrink={0}
            >
              40%
            </Typography>
            <Box flexGrow={1}>
              <CustomProgress
                value={40}
                variant="determinate"
                sx={{
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#FD8B05',
                  },
                }}
              />
            </Box>
          </Box>
        </Box>
        <Box>
          <Typography className="text-heading-secondary" component={'h4'}>
            1.3. Sáng tạo - Hoạt bát - Lạc quan
          </Typography>
          <Box mt={2.5} ml={1} display={'flex'} alignItems={'center'}>
            <Typography
              component={'span'}
              width={40}
              fontSize={12}
              fontWeight={500}
              flexShrink={0}
            >
              50%
            </Typography>
            <Box flexGrow={1}>
              <CustomProgress
                value={50}
                variant="determinate"
                sx={{
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#FD057C',
                  },
                }}
              />
            </Box>
          </Box>
        </Box>
        <Box>
          <Typography className="text-heading-secondary" component={'h4'}>
            1.4. Cẩn thận - Cầu toàn - Thực tế
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
          <Typography className="text-heading-secondary" component={'h4'}>
            1.5. Năng động - Linh hoạt - Tò mò
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
          <Typography className="text-heading-secondary" component={'h4'}>
            1.6. Quan tâm - Yêu thương - Kiểm soát
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
          <Typography className="text-heading-secondary" component={'h4'}>
            1.7. Thông thái - Khám phá - Truyền đạt
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
          <Typography className="text-heading-secondary" component={'h4'}>
            1.8. Công bằng - Tập trung - Lý tưởng
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
          <Typography className="text-heading-secondary" component={'h4'}>
            1.9. Trách nhiệm - Rộng lượng - Hào phóng
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
