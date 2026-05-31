import { Box, Container, Divider, Typography } from '@mui/material'

import { IconHome2 } from '@/components/icon'

export interface BannerPostProps {
  title: string
}

export default function BannerPost({ title }: BannerPostProps) {
  return (
    <Box id="banner-article">
      <Container maxWidth={false}>
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            transform: 'translateY(-50%)',
          }}
        >
          <Typography component={'h3'} className="text-heading">
            {title}
          </Typography>
          <Box
            mt={3}
            sx={{
              display: 'flex',
              columnGap: '10px',
              alignItems: 'center',
            }}
          >
            <IconHome2 />
            <Box
              display={'flex'}
              alignItems={'center'}
              color={(theme) => theme.palette.grey[500]}
            >
              <Typography component={'span'}>Home</Typography>
              <Divider
                orientation="vertical"
                variant="middle"
                flexItem
                sx={{
                  borderColor: (theme) => theme.palette.grey[500],
                  height: '13px',
                  marginLeft: 1,
                  marginRight: 1,
                }}
              />
              <Typography component={'span'} fontWeight={600}>
                Single Post
              </Typography>
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
