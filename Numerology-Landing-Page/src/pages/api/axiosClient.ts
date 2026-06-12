import axios from 'axios'
import Cookies from 'js-cookie'

import { tryRefreshTokens } from '@/lib/token-refresh'
import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE } from '@/lib/user-auth'

export const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE ??
  process.env.BASE_URL ??
  'http://localhost:8000'

const axiosClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosClient.interceptors.request.use(
  (config) => {
    const accessToken = Cookies.get(ACCESS_TOKEN_COOKIE)
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error || {}
    if (response?.status === 401 && typeof window !== 'undefined') {
      const url: string = config?.url ?? ''
      // Access token likely expired — try a one-time refresh, then replay once.
      if (
        config &&
        !config._retry &&
        !url.includes('/auth/refresh') &&
        Cookies.get(REFRESH_TOKEN_COOKIE)
      ) {
        config._retry = true
        const refreshed = await tryRefreshTokens()
        if (refreshed) {
          const newToken = Cookies.get(ACCESS_TOKEN_COOKIE)
          if (newToken) {
            config.headers = config.headers ?? {}
            config.headers.Authorization = `Bearer ${newToken}`
          }
          return axiosClient(config)
        }
      }
      Cookies.remove(ACCESS_TOKEN_COOKIE)
      Cookies.remove(REFRESH_TOKEN_COOKIE)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default axiosClient
