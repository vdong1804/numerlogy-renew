import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import { Box, Fab } from '@mui/material'
import type { ReactNode } from 'react'

import ScrollTop from '@/components/common/ScrollTop'

import Footer from './Footer'
import Header from './Header'

type IMainProps = {
  meta: ReactNode
  children: ReactNode
}

const Main = (props: IMainProps) => {
  return (
    <Box sx={{ width: '100%' }} id="wrapper" component={'main'}>
      {props.meta}
      <Header />
      {props.children}
      <Footer />
      <ScrollTop {...props}>
        <Fab size="medium" aria-label="scroll back to top">
          <KeyboardArrowUpIcon sx={{ width: 32, height: 32 }} />
        </Fab>
      </ScrollTop>
    </Box>
  )
}

export { Main }
