'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { loginWithCredentials, User } from './lib/supabase'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  // Přesměruj na dashboard pokud je uživatel přihlášen
  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      router.push('/dashboard')
    }
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const { user: loggedUser, error: loginError } = await loginWithCredentials(username, password)

    setLoading(false)

    if (loginError) {
      setError(loginError)
      return
    }

    if (loggedUser) {
      localStorage.setItem('user', JSON.stringify(loggedUser))
      router.push('/dashboard')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Webomat CRM</h1>
        <p className="subtitle">Přihlaste se do systému</p>
        <form onSubmit={handleLogin}>
          <div className="field">
            <label htmlFor="username">Uživatel</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Zadejte uživatelské jméno"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Heslo</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Zadejte heslo"
              required
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Přihlašuji...' : 'Přihlásit se'}
          </button>
        </form>
      </div>
    </div>
  )
}
