import SearchIcon from '@mui/icons-material/Search'
import {
  alpha,
  Box,
  Dialog,
  DialogContent,
  IconButton,
  InputBase,
  Slide,
  styled,
} from '@mui/material'
import type { TransitionProps } from '@mui/material/transitions'
import React, { useState } from 'react'
// Search
const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: '9999px',
  backgroundColor: alpha(theme.palette.common.white, 0.2),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.white, 0.3),
  },
  marginLeft: 0,
  width: '100%',
  display: 'flex',
}))

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: '#fff',
  fontSize: '18px',
  fontWeight: 500,
  width: '100%',
  '& .MuiInputBase-input': {
    padding: theme.spacing(2, 0, 2, 4),
    paddingRight: `calc(1em + ${theme.spacing(2)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
  },
}))

// Transition Modal Search
const TransitionModal = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement<any, any>
  },
  ref: React.Ref<unknown>
) {
  return <Slide direction="down" ref={ref} {...props} />
})

export interface IModalSearchProps {
  open: boolean
  handleClose: () => void
  onSubmit?: () => void
}

export default function ModalSearch({
  open,
  handleClose,
  onSubmit = () => {},
}: IModalSearchProps) {
  const [inputValue, setInputValue] = useState('')
  return (
    <Dialog
      open={open}
      TransitionComponent={TransitionModal}
      onClose={handleClose}
      disableScrollLock={true}
      maxWidth="md"
      aria-describedby="modal search"
      PaperProps={{
        sx: {
          bgcolor: '#031E30',
          maxWidth: 'revert',
          width: 1000,
          borderRadius: 2.5,
          top: -100,
        },
      }}
    >
      <DialogContent sx={{ p: 6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <Search>
            <StyledInputBase
              type="search"
              placeholder="Tìm kiếm..."
              inputProps={{ 'aria-label': 'search' }}
              autoFocus={true}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  onSubmit?.()
                  handleClose()
                }
              }}
            />
            <IconButton sx={{ p: 2 }} color="primary" onClick={onSubmit}>
              <SearchIcon fontSize="large" color="primary" />
            </IconButton>
          </Search>
        </Box>
      </DialogContent>
    </Dialog>
  )
}
