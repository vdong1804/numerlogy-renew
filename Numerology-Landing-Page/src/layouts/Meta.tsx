/**
 * Meta layout — dynamic OG/Twitter/canonical/JSON-LD per page.
 * Extended from base version; backward-compatible (title + description still required).
 */
import Head from 'next/head'
import { useRouter } from 'next/router'
import { NextSeo } from 'next-seo'

import { AppConfig } from '@/utils/AppConfig'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://nhansinhquan.vn'
const DEFAULT_OG_IMAGE = `${SITE_URL}/og-default.png`

type IMetaProps = {
  title: string
  description: string
  canonical?: string
  /** OG image URL — defaults to /og-default.png */
  image?: string
  /** 'website' | 'article' | 'product' — defaults to 'website' */
  type?: string
  /** JSON-LD structured data object — rendered as application/ld+json */
  jsonLd?: Record<string, unknown>
}

const Meta = (props: IMetaProps) => {
  const router = useRouter()
  const canonical = props.canonical ?? `${SITE_URL}${router.asPath.split('?')[0]}`
  const image = props.image ?? DEFAULT_OG_IMAGE
  const type = props.type ?? 'website'

  return (
    <>
      <Head>
        <meta charSet="UTF-8" key="charset" />
        <meta
          name="viewport"
          content="width=device-width,initial-scale=1"
          key="viewport"
        />
        <link
          rel="icon"
          type="image/svg+xml"
          href={`${router.basePath}/numerology_favicon.svg`}
          key="icon-svg"
        />
        <link
          rel="icon"
          type="image/png"
          sizes="32x32"
          href={`${router.basePath}/favicon-32x32.png`}
          key="icon32"
        />
        <link
          rel="apple-touch-icon"
          sizes="180x180"
          href={`${router.basePath}/apple-touch-icon.png`}
          key="apple-touch"
        />
        <link rel="manifest" href={`${router.basePath}/manifest.json`} key="manifest" />

        {/* Twitter card */}
        <meta name="twitter:card" content="summary_large_image" key="tw-card" />
        <meta name="twitter:title" content={props.title} key="tw-title" />
        <meta name="twitter:description" content={props.description} key="tw-desc" />
        <meta name="twitter:image" content={image} key="tw-image" />

        {/* JSON-LD per-page structured data */}
        {props.jsonLd && (
          <script
            key="json-ld"
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(props.jsonLd) }}
          />
        )}
      </Head>

      <NextSeo
        title={props.title}
        description={props.description}
        canonical={canonical}
        openGraph={{
          title: props.title,
          description: props.description,
          url: canonical,
          type,
          locale: AppConfig.locale,
          site_name: AppConfig.site_name,
          images: [{ url: image, width: 1200, height: 630, alt: props.title }],
        }}
      />
    </>
  )
}

export { Meta }
