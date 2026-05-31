import { Backdrop, Box } from '@mui/material'

interface LoadingProps {
  isOpen: boolean
}
export default function Loading({ isOpen }: LoadingProps) {
  return (
    <Backdrop
      sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
      open={isOpen}
      // onClick={handleClose}
    >
      {/* <CircularProgress color="primary" /> */}
      <Box className="loader"></Box>
    </Backdrop>
  )
}
