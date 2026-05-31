import { Box } from '@mui/material'
import { useRouter } from 'next/router'
import type { ReactElement } from 'react'
import useSWR from 'swr'

import NotFound404 from '@/components/common/NotFound404'
import { Loading } from '@/components/loading'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import { BannerPost, PostContent } from '@/modules/post'

import numerologyApi from '../api/numerologyApi'

const ArticleDetail: NextPageWithLayout = () => {
  const router = useRouter()
  const {
    data: postDetail,
    isLoading,
    error,
  } = useSWR(router.query.id ? 'post-detail' : '', () =>
    numerologyApi.getDetailNews(router.query.id as string)
  )
  if (error) return <NotFound404 />
  return (
    <Box className="blog-post-page-wrapper">
      <Loading isOpen={isLoading} />
      <BannerPost title={postDetail?.title || ''} />
      <PostContent />
    </Box>
  )
}
ArticleDetail.getLayout = function getLayout(page: ReactElement) {
  return (
    <Main
      meta={<Meta title="Chi tiết bài viết" description="Chi tiết bài viết" />}
    >
      {page}
    </Main>
  )
}

export default ArticleDetail
