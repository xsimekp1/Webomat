'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import ApiClient from '../lib/api'

interface CRMStats {
  total_leads: number
  follow_ups_today: number
}

export default function DashboardPage() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<CRMStats | null>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      ApiClient.getCRMStats()
        .then(setStats)
        .catch(() => {})
    }
  }, [isAuthenticated])

  if (isLoading || !user) {
    return <div className="loading">Načítám...</div>
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Webomat CRM</h1>
        </div>
        <div className="header-right">
          <span className="user-info">
            {user.name} ({user.role === 'admin' ? 'Admin' : 'Obchodník'})
          </span>
           <button onClick={() => router.push('/help')} className="btn-help">
             Nápověda
           </button>
           <button onClick={() => router.push('/dashboard/profile')} className="btn-profile">
             Můj profil
           </button>
           <button onClick={logout} className="btn-logout">
             Odhlásit
           </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="welcome-section">
          <h2>Vítej, {user.name}!</h2>
          <p>Toto je tvůj přehled. Brzy zde uvidíš důležité informace.</p>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <h3>Leady</h3>
            <p className="stat-value">{stats?.total_leads ?? '--'}</p>
            <p className="stat-label">Celkem v systému</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📞</div>
            <h3>Dnes volat</h3>
            <p className="stat-value">{stats?.follow_ups_today ?? '--'}</p>
            <p className="stat-label">Naplánované hovory</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💼</div>
            <h3>Aktivní dealy</h3>
            <p className="stat-value">--</p>
            <p className="stat-label">V řešení</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <h3>Provize</h3>
            <p className="stat-value">-- Kč</p>
            <p className="stat-label">Tento měsíc</p>
          </div>
        </div>

        <div className="sections-grid">
          <section className="section-card">
            <h3>🎯 CRM Pipeline</h3>
            <p>Správa leadů a obchodních příležitostí</p>
            <ul>
              <li>Nový → Voláno → Zájem → Nabídka → Won/Lost</li>
              <li>Seznam firem k obvolání</li>
              <li>Historie komunikace</li>
            </ul>
            <button
              onClick={() => router.push('/dashboard/crm')}
              className="btn-admin"
            >
              Otevřít CRM
            </button>
          </section>

          <section className="section-card">
            <h3>🌐 Weby</h3>
            <p>Generování a správa webů klientů</p>
            <ul>
              <li>Šablony pro různé segmenty</li>
              <li>Rychlé nasazení</li>
              <li>Verzování a rollback</li>
            </ul>
            <span className="coming-soon">Připravujeme...</span>
          </section>

          <section className="section-card">
            <h3>📋 Úkoly</h3>
            <p>Co je potřeba udělat dnes</p>
            <ul>
              <li>Follow-up hovory</li>
              <li>Odeslat nabídky</li>
              <li>Připomenout platby</li>
            </ul>
            <span className="coming-soon">Připravujeme...</span>
          </section>

          {user.role === 'admin' && (
            <section className="section-card admin-card">
              <h3>Administrace</h3>
              <p>Správa systému a uživatelů</p>
              <ul>
                <li>Správa uživatelů</li>
                <li>Přehled provizí</li>
                <li>Nastavení balíčků</li>
              </ul>
              <button
                onClick={() => router.push('/dashboard/admin')}
                className="btn-admin"
              >
                Spravovat uživatele
              </button>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
