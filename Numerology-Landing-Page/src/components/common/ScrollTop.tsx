import { Box, Fade, useScrollTrigger } from '@mui/material'

interface Props {
  /**
   * Injected by the documentation to work in an iframe.
   * You won't need it on your project.
   */
  window?: () => Window
  children: React.ReactElement
}

export default function ScrollTop(props: Props) {
  const { children, window } = props
  // Note that you normally won't need to set the window ref as useScrollTrigger
  // will default to window.
  // This is only being set here because the demo is in an iframe.
  const trigger = useScrollTrigger({
    target: window ? window() : undefined,
    disableHysteresis: true,
    threshold: 100,
  })

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const anchor = (
      (event.target as HTMLDivElement).ownerDocument || document
    ).querySelector('body')

    if (anchor) {
      anchor.scrollIntoView({ block: 'start', behavior: 'smooth' })
    }
  }

  return (
    <Fade in={trigger}>
      <Box
        onClick={handleClick}
        role="presentation"
        sx={{
          position: 'fixed',
          bottom: {
            xs: 5,
            lg: 16,
          },
          right: {
            xs: 5,
            lg: 32,
          },
          zIndex: 100,
        }}
      >
        {children}
      </Box>
    </Fade>
  )
}
