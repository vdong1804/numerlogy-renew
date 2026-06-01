import type { ReactElement } from 'react'

import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import { BlogArticleDetail } from '@/modules/blog'

const BlogDetailPage: NextPageWithLayout = () => {
  return <BlogArticleDetail />
}

BlogDetailPage.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={
        <Meta
          title="Chi tiết bài viết | Blog thần số học"
          description="Bài viết chuyên sâu về thần số học Pythagoras."
        />
      }
    >
      {page}
    </Main>
  )
}

export default BlogDetailPage
