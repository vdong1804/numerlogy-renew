import type { ReactElement } from 'react'
import React from 'react'

import NotFound404 from '@/components/common/NotFound404'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'

const Custom404: NextPageWithLayout = () => {
  return <NotFound404 />
}
Custom404.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main meta={<Meta title="not found" description="not found" />}>
      {page}
    </Main>
  )
}

export default Custom404
