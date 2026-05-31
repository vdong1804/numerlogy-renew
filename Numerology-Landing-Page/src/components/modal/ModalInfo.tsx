import CloseIcon from '@mui/icons-material/Close'
import Dialog from '@mui/material/Dialog'
import DialogContent from '@mui/material/DialogContent'
import IconButton from '@mui/material/IconButton'
import { styled } from '@mui/material/styles'
import type { ReactNode } from 'react'

const MODAL_INFO_WIDTH = '485px'
const ModalCustom = styled(Dialog)(({ theme }) => ({
  '& .MuiDialogContent-root': {
    padding: theme.spacing(4),
  },
}))

interface ModalInfoProps {
  open: boolean
  handleClose: () => void
  children: ReactNode
}

export default function ModalInfo({
  open,
  handleClose,
  children,
}: ModalInfoProps) {
  return (
    <ModalCustom
      onClose={handleClose}
      aria-labelledby="Modal Info"
      open={open}
      disableScrollLock={true}
      PaperProps={{
        sx: {
          borderRadius: 5,
          width: MODAL_INFO_WIDTH,
          color: (theme) => theme.palette.common.black,
          top: -50,
        },
      }}
    >
      <IconButton
        aria-label="close"
        onClick={handleClose}
        sx={{
          position: 'absolute',
          right: 16,
          top: 16,
          color: (theme) => theme.palette.grey[500],
          bgcolor: (theme) => theme.palette.grey[100],
          zIndex: 10,
        }}
      >
        <CloseIcon sx={{ color: '#475866' }} />
      </IconButton>
      <DialogContent>{children}</DialogContent>
    </ModalCustom>
  )
}
