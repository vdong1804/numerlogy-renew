import type { ReactElement } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import { BlogList } from '@/modules/blog'

const BlogPage: NextPageWithLayout = () => {
  return <BlogList />
}

BlogPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta
          title="Blog tra cứu thần số học"
          description="Kiến thức, hướng dẫn và góc nhìn chuyên sâu về thần số học Pythagoras."
        />
      }
    >
      {page}
    </Main>
  )
}

export default BlogPage
