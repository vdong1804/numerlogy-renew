import { Box, Container, Typography } from '@mui/material'
import Image from 'next/image'
import * as React from 'react'

import { IconListItem } from '@/components/icon'

import { TittlePage } from './parts'

export default function TeacherInfo() {
  const TEACHER_DESCRIPTION = [
    {
      id: 1,
      content:
        'CEO Tra cứu thần số học Aladanh Thành – Nhà nghiên cứu thần số học',
    },
    {
      id: 2,
      content: 'Nhà sáng lập hệ thống Tra cứu thần số học hàng đầu Việt Nam',
    },
    {
      id: 3,
      content: 'Hơn 7 năm nghiên cứu và ứng dụng Nhân số học vào đời sống',
    },
    {
      id: 4,
      content: 'Hơn 100 khóa đào tạo thần số học cho đại chúng Việt Nam',
    },
    {
      id: 5,
      content:
        'Cố vấn định hướng cho hơn 50 doanh nghiệp lớn nhỏ trong kỷ nguyên chuyển đổi số',
    },
  ]
  return (
    <Box className="teacher-info-wrapper" id="thong-tin-aladash">
      <Container maxWidth={false}>
        <Box
          sx={{
            display: 'inline-flex',
            gap: 8,
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Box
            sx={{
              marginTop: {
                xs: 4,
                lg: 0,
              },
            }}
          >
            <TittlePage>Nhà nghiên cứu thần số học Pitago</TittlePage>
            <Typography mt={2.5} className="name-teacher-heading">
              <Typography
                display={'inline'}
                color="primary"
                component={'span'}
                sx={{
                  fontFamily: 'var(--philosopher-font)',
                  fontSize: 32,
                  lineHeight: '70px',
                }}
              >
                Thầy{' '}
              </Typography>
              Aladanh Thành
            </Typography>
            <Box
              mt={4}
              ml={2}
              display={'flex'}
              flexDirection={'column'}
              rowGap={2}
            >
              {TEACHER_DESCRIPTION.map(({ id, content }) => {
                return (
                  <Box
                    key={id}
                    sx={{ display: 'flex', columnGap: 2, alignItems: 'center' }}
                  >
                    <IconListItem />
                    <Typography>{content}</Typography>
                  </Box>
                )
              })}
            </Box>
          </Box>
          <Box
            sx={{
              width: '40%',
              display: {
                xs: 'none',
                md: 'flex',
              },
            }}
          >
            <Image
              src="/assets/images/bg-teacher.png"
              alt="Thầy Aladanh Thành – nhà nghiên cứu thần số học"
              width={600}
              height={700}
              style={{ width: '100%', height: 'auto' }}
              priority
            />
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
