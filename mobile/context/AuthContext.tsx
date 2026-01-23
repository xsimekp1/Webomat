import React, { createContext, useContext, useState, useEffect } from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { ApiClient } from '../lib/api'
import type { User } from '@/shared/types'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await ApiClient.login(username, password)
      const accessToken = response.access_token

      await AsyncStorage.setItem('token', accessToken)
      setToken(accessToken)

      // Fetch user profile
      const userData = await ApiClient.getUserProfile()
      setUser(userData)
      await AsyncStorage.setItem('user', JSON.stringify(userData))

      return { success: true }
    } catch (error: any) {
      console.error('Login error:', error)
      const errorMessage = error.response?.data?.detail || 'Přihlášení se nezdařilo'
      return { success: false, error: errorMessage }
    }
  }

  const logout = async () => {
    await AsyncStorage.removeItem('token')
    await AsyncStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  const initializeAuth = async () => {
    try {
      const savedToken = await AsyncStorage.getItem('token')
      const savedUser = await AsyncStorage.getItem('user')

      if (savedToken && savedUser) {
        setToken(savedToken)
        try {
          // Verify token is still valid
          const userData = await ApiClient.getUserProfile()
          setUser(userData)
          await AsyncStorage.setItem('user', JSON.stringify(userData))
        } catch (error) {
          // Token is invalid, clear auth state
          console.error('Token validation failed:', error)
          await logout()
        }
      }
    } catch (error) {
      console.error('Error initializing auth:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    initializeAuth()
  }, [])

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
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