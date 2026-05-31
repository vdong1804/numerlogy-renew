import { Box, Button, Typography } from '@mui/material'

import { IconPDF } from '@/components/icon'

export interface BoxExportPDFProps {
  onClick?: () => void
}

export default function BoxExportPDF({
  onClick = () => {},
}: BoxExportPDFProps) {
  return (
    <Box
      p={2.5}
      bgcolor={(theme) => theme.palette.common.white}
      borderRadius={2.5}
      position={'relative'}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        rowGap: 1.25,
      }}
    >
      <Box sx={{ display: 'flex', columnGap: 1.25, alignItems: 'center' }}>
        <IconPDF />
        <Typography
          color="common.black"
          variant="h3"
          className="font-philosopher"
        >
          File báo cáo thần số sọc của bạn
        </Typography>
      </Box>
      <Typography color="common.black" fontStyle={'italic'} maxWidth={440}>
        Bằng cách nâng cấp VIP, bạn có thể tải về file tổng hợp thần số học của
        bạn để sử dụng lâu dài.
      </Typography>

      <Box
        sx={{
          position: {
            md: 'absolute',
          },
          right: 58,
          top: '50%',
          transform: {
            md: 'translateY(-50%)',
          },
        }}
      >
        <Button onClick={onClick} variant="contained">
          Download
        </Button>
      </Box>
    </Box>
  )
}
