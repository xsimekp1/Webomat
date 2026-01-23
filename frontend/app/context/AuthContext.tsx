'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import ApiClient from '../lib/api'

export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'sales'
  is_active: boolean
  phone?: string
  must_change_password: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    router.push('/')
  }, [router])

  const refreshUser = useCallback(async () => {
    try {
      const userData = await ApiClient.getUserProfile()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Failed to refresh user:', error)
      logout()
    }
  }, [logout])

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('token')
      const savedUser = localStorage.getItem('user')

      if (savedToken && savedUser) {
        setToken(savedToken)
        try {
          // Verify token is still valid by fetching user profile
          const userData = await ApiClient.getUserProfile()
          setUser(userData)
          localStorage.setItem('user', JSON.stringify(userData))
        } catch (error) {
          // Token is invalid, clear auth state
          console.error('Token validation failed:', error)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await ApiClient.login(username, password)
      const accessToken = response.access_token

      localStorage.setItem('token', accessToken)
      setToken(accessToken)

      // Fetch user profile
      const userData = await ApiClient.getUserProfile()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))

      return { success: true }
    } catch (error: any) {
      console.error('Login error:', error)
      const errorMessage = error.response?.data?.detail || 'Nastala neočekávaná chyba'
      return { success: false, error: errorMessage }
    }
  }

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
