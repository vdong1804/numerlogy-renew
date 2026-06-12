import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'
import { Box, Button, Typography } from '@mui/material'

import { IconPDF } from '@/components/icon'

export interface BoxExportPDFProps {
  /** Paid viewers download the full fulfilled report; free get the reduced PDF. */
  isPaid?: boolean
  onClick?: () => void
  /** When provided, renders a persistent banner inviting the user to ask the
   *  AI assistant follow-up questions about this report. */
  onChatClick?: () => void
}

export default function BoxExportPDF({
  isPaid = false,
  onClick = () => {},
  onChatClick,
}: BoxExportPDFProps) {
  return (
    <Box
      p={2.5}
      bgcolor={(theme) => theme.palette.common.white}
      borderRadius={2.5}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        rowGap: 1.5,
      }}
    >
      {/* Download block — keep the absolute CTA scoped to this section only. */}
      <Box
        position={'relative'}
        sx={{ display: 'flex', flexDirection: 'column', rowGap: 1.25 }}
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

      {/* Persistent AI-chat nudge: hỏi đáp với Trợ lý AI về báo cáo này. */}
      {onChatClick && (
        <Box
          sx={{
            borderTop: '1px dashed',
            borderColor: 'rgba(0, 0, 0, 0.12)',
            pt: 1.5,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            columnGap: 1.5,
            rowGap: 1,
          }}
        >
          <Box
            sx={{ display: 'flex', alignItems: 'center', columnGap: 1, flex: 1 }}
          >
            <ChatBubbleOutlineIcon sx={{ color: 'primary.main' }} />
            <Typography color="common.black">
              Có thắc mắc về các chỉ số? Hỏi đáp trực tiếp với Trợ lý AI để được
              giải thích chi tiết.
            </Typography>
          </Box>
          <Button
            onClick={onChatClick}
            variant="outlined"
            startIcon={<ChatBubbleOutlineIcon />}
            sx={{
              // Theme sets a global white button text color; force the brand
              // color here so the outlined button is legible on the white card.
              color: 'primary.main',
              borderColor: 'primary.main',
              flexShrink: 0,
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'rgba(249, 106, 45, 0.08)',
              },
            }}
          >
            Chat với AI
          </Button>
        </Box>
      )}
    </Box>
  )
}
