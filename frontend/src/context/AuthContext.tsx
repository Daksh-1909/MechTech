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
  register: (
    name: string,
    email: string,
    password: string,
    organizationName?: string,
  ) => Promise<any>
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
      const currentUser = await api.get<User>('/auth/me')
      setUser(currentUser)
      setOrganization(currentUser.organizations[0] ?? null)
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
      const res = await api.post<{ user: User }>('/auth/login', {
        email,
        password,
      })
      setUser(res.user)
      setOrganization(res.user.organizations[0] ?? null)
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

  const register = async (
    name: string,
    email: string,
    password: string,
    organizationName?: string,
  ) => {
    return api.post('/auth/register', {
      display_name: name,
      email,
      password,
      organization_name: organizationName,
    })
  }

  const hasRole = (roleKey: string) => {
    if (!user) return false
    return user.roles.includes(roleKey)
  }

  const isPlatformAdmin = Boolean(hasRole('platform_admin') || hasRole('admin'))
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
