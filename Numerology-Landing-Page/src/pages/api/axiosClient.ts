import axios from 'axios'
import Cookies from 'js-cookie'

import { ACCESS_TOKEN_COOKIE } from '@/lib/user-auth'

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
  (error) => {
    const { response } = error || {}
    if (response?.status === 401 && typeof window !== 'undefined') {
      Cookies.remove(ACCESS_TOKEN_COOKIE)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default axiosClient
