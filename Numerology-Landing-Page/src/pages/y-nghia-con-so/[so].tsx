import type { GetStaticPaths, GetStaticProps } from 'next'
import type { ReactElement } from 'react'

import NotFound404 from '@/components/common/NotFound404'
import { Main } from '@/layouts/Main'
import { Meta } from '@/layouts/Meta'
import type { NextPageWithLayout } from '@/models'
import {
  getMeaningBySlug,
  NUMBER_MEANINGS,
  NumberMeaningDetail,
} from '@/modules/numerology-meaning'
import type { NumberMeaning } from '@/modules/numerology-meaning'

interface NumberMeaningPageProps {
  meaning: NumberMeaning | null
}

const NumberMeaningPage: NextPageWithLayout<NumberMeaningPageProps> = ({
  meaning,
}) => {
  if (!meaning) return <NotFound404 />
  return <NumberMeaningDetail meaning={meaning} />
}

NumberMeaningPage.getLayout = function getLayout(page: ReactElement) {
  // Access the resolved meaning via the rendered element's props for meta.
  const meaning = (page.props as NumberMeaningPageProps).meaning
  const title = meaning
    ? `Số ${meaning.number} – ${meaning.title} | Ý nghĩa các con số`
    : 'Ý nghĩa các con số trong thần số học'
  const description = meaning
    ? meaning.summary
    : 'Khám phá ý nghĩa các con số trong thần số học Pythagoras.'
  return (
    <Main meta={<Meta title={title} description={description} />}>{page}</Main>
  )
}

// Static export: pre-render one page per known number slug.
export const getStaticPaths: GetStaticPaths = async () => ({
  paths: NUMBER_MEANINGS.map((m) => ({ params: { so: m.slug } })),
  fallback: false,
})

export const getStaticProps: GetStaticProps<NumberMeaningPageProps> = async ({
  params,
}) => {
  const meaning = getMeaningBySlug(params?.so) ?? null
  if (!meaning) return { notFound: true }
  return { props: { meaning } }
}

export default NumberMeaningPage
