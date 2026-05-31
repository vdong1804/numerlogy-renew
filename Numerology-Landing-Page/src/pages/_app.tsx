import '@/styles/main.scss'
import '@/styles/admin.css'

import type { EmotionCache } from '@emotion/react'
import { CacheProvider } from '@emotion/react'
import { CssBaseline } from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import { LocalizationProvider } from '@mui/x-date-pickers'
import type { AppProps } from 'next/app'
import type { ReactElement } from 'react'

import Analytics from '@/components/analytics'
import CookieConsent from '@/components/cookie-consent'
import type { NextPageWithLayout } from '@/models'
import lightThemeOptions from '@/styles/theme/light-theme-option'
import createEmotionCache from '@/utils/createEmotionCache'
import CustomDateAdapter from '@/utils/helpers'

const clientSideEmotionCache = createEmotionCache()

type AppPropsWithLayout = AppProps & {
  Component: NextPageWithLayout
  emotionCache: EmotionCache
}

const lightTheme = createTheme(lightThemeOptions)
const MyApp = ({
  Component,
  emotionCache = clientSideEmotionCache,
  pageProps,
}: AppPropsWithLayout) => {
  const getLayout = Component.getLayout ?? ((page: ReactElement) => page)
  return (
    <LocalizationProvider
      dateFormats={{ monthShort: 'T.M', monthAndYear: 'MM/YYYY' }}
      // @ts-ignore
      dateAdapter={CustomDateAdapter}
    >
      <CacheProvider value={emotionCache}>
        <ThemeProvider theme={lightTheme}>
          <CssBaseline />
          {getLayout(<Component {...pageProps} />)}
          {/* Analytics: loads GA4/Pixel only after consent granted */}
          <Analytics />
          {/* Cookie consent banner — hidden once consent stored (365d) */}
          <CookieConsent />
        </ThemeProvider>
      </CacheProvider>
    </LocalizationProvider>
  )
}

export default MyApp
