import { Box, Button, Typography } from '@mui/material'

import { IconPDF } from '@/components/icon'

export interface BoxExportPDFProps {
  /** Paid viewers download the full fulfilled report; free get the reduced PDF. */
  isPaid?: boolean
  onClick?: () => void
}

export default function BoxExportPDF({
  isPaid = false,
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
          File báo cáo thần số học của bạn
        </Typography>
      </Box>
      <Typography color="common.black" fontStyle={'italic'} maxWidth={440}>
        {isPaid
          ? 'Tải về file báo cáo đầy đủ của bạn để sử dụng lâu dài.'
          : 'Tải bản tóm tắt miễn phí. Mở khóa báo cáo đầy đủ để nhận file chi tiết toàn bộ chỉ số.'}
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
          {isPaid ? 'Tải báo cáo đầy đủ' : 'Tải bản tóm tắt'}
        </Button>
      </Box>
    </Box>
  )
}
