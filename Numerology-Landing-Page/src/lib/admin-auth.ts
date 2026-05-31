/**
 * Admin authentication hook
 * Reads token from localStorage, verifies is_superuser via /auth/me
 */

import { useRouter } from 'next/router'
import { useCallback, useEffect, useState } from 'react'

import { clearAdminToken, getJson } from './admin-api'

export interface AdminUser {
  id: number
  email: string
  full_name: string
  is_superuser: boolean
  is_active: boolean
}

interface UseAdminAuthReturn {
  user: AdminUser | null
  loading: boolean
  logout: () => void
}

export function useAdminAuth(): UseAdminAuthReturn {
  const router = useRouter()
  const [user, setUser] = useState<AdminUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token =
      typeof window !== 'undefined'
        ? localStorage.getItem('admin_access_token')
        : null

    if (!token) {
      router.replace('/admin/login')
      setLoading(false)
      return
    }

    getJson<AdminUser>('/auth/me')
      .then((me) => {
        if (!me.is_superuser) {
          clearAdminToken()
          router.replace('/admin/login')
          return
        }
        setUser(me)
      })
      .catch(() => {
        clearAdminToken()
        router.replace('/admin/login')
      })
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const logout = useCallback(() => {
    clearAdminToken()
    setUser(null)
    router.push('/admin/login')
  }, [router])

  return { user, loading, logout }
}
