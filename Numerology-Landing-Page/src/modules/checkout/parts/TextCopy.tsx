import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import { Box, Typography } from '@mui/material'
import Tooltip from '@mui/material/Tooltip'
import type { SxProps } from '@mui/system'

import { useCopyToClipboard } from '@/hooks'

export interface TextCopyProps {
  title: string
  sx?: SxProps
}

export default function TextCopy({ title, sx }: TextCopyProps) {
  // eslint-disable-next-line unused-imports/no-unused-vars
  const [value, copy] = useCopyToClipboard()
  return (
    <Box display="flex" alignItems="center">
      <Typography color="text.secondary" sx={sx}>
        {title}
      </Typography>

      <Tooltip title={'Copy to Clipboard'}>
        <ContentCopyIcon
          onClick={() => copy(title)}
          className="ml-4 transition-colors cursor-pointer text-gray-label-checkout hover:text-gray-600"
          sx={{
            ml: 2,
            width: 22,
            cursor: 'pointer',
            color: '#8D8D8D',
            '&:hover': {
              color: (theme) => theme.palette.grey[600],
            },
          }}
        />
      </Tooltip>
    </Box>
  )
}
