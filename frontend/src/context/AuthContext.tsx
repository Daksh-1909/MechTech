import React, { createContext, useContext, useEffect, useState } from 'react'
import { api, ApiError } from '../lib/api'
import type { Organization, User } from '../types/api'

interface AuthContextType {
  user: User | null
  organization: Organization | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (name: string, email: string, password: string, organizationName?: string) => Promise<any>
  refreshUser: () => Promise<void>
  hasRole: (roleKey: string) => boolean
  isPlatformAdmin: boolean
  isMaintainer: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [organization, setOrganization] = useState<Organization | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refreshUser = async () => {
    try {
      const data = await api.get<{ user: User; organization?: Organization }>('/auth/me')
      setUser(data.user)
      if (data.organization) {
        setOrganization(data.organization)
      } else if (data.user.organization_id) {
        try {
          const org = await api.get<Organization>(`/organizations/${data.user.organization_id}`)
          setOrganization(org)
        } catch {
          // ignore org fetch error
        }
      }
      setError(null)
    } catch (err: any) {
      setUser(null)
      setOrganization(null)
      // Only set error if not 401 unauthenticated
      if (err instanceof ApiError && err.status !== 401) {
        setError(err.message)
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refreshUser()
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await api.post<{ user: User; organization?: Organization }>('/auth/login', {
        email,
        password,
      })
      setUser(res.user)
      if (res.organization) {
        setOrganization(res.organization)
      } else if (res.user.organization_id) {
        try {
          const org = await api.get<Organization>(`/organizations/${res.user.organization_id}`)
          setOrganization(org)
        } catch {
          // ignore
        }
      }
    } catch (err: any) {
      const msg = err.message || 'Login failed. Please check your credentials.'
      setError(msg)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      setUser(null)
      setOrganization(null)
    }
  }

  const register = async (name: string, email: string, password: string, organizationName?: string) => {
    return api.post('/auth/register', {
      name,
      email,
      password,
      organization_name: organizationName,
    })
  }

  const hasRole = (roleKey: string) => {
    if (!user) return false
    if (user.is_superuser) return true
    if (user.roles?.includes(roleKey)) return true
    return user.assigned_roles?.some((r) => r.role.key === roleKey) ?? false
  }

  const isPlatformAdmin = Boolean(user?.is_superuser || hasRole('platform_admin') || hasRole('admin'))
  const isMaintainer = Boolean(isPlatformAdmin || hasRole('maintainer') || hasRole('org_admin'))

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        logout,
        register,
        refreshUser,
        hasRole,
        isPlatformAdmin,
        isMaintainer,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

