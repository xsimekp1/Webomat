'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import { useTranslations } from 'next-intl'

export default function LoginPage() {
  const t = useTranslations('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const { isAuthenticated, isLoading, login } = useAuth()

  // Přesměruj na dashboard pokud je uživatel přihlášen
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, isLoading, router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(username, password)

    setLoading(false)

    if (!result.success) {
      setError(result.error || t('invalidCredentials'))
      return
    }

    router.push('/dashboard')
  }

  return (
    <div className="container">
      <div className="card login-container">
        <h1 className="login-title">Webomat CRM</h1>
        <p className="subtitle login-subtitle">{t('subtitle')}</p>
        <form onSubmit={handleLogin}>
          <div className="field login-form-field form-progressive-1">
            <label htmlFor="username">{t('username')}</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={t('usernamePlaceholder')}
              required
            />
          </div>
          <div className="field login-form-field form-progressive-2">
            <label htmlFor="password">{t('password')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('passwordPlaceholder')}
              required
            />
          </div>
          {error && <p className="error login-form-field form-progressive-3">{error}</p>}
          <button type="submit" className="btn login-submit-btn" disabled={loading}>
            {loading ? t('signingIn') : t('signIn')}
          </button>
        </form>
      </div>
    </div>
  )
}