'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { User } from '../lib/supabase'

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null)
  const router = useRouter()

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    } else {
      router.push('/')
    }
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('user')
    router.push('/')
  }

  if (!user) {
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
          <button onClick={() => router.push('/dashboard/profile')} className="btn-profile">
            Můj profil
          </button>
          <button onClick={handleLogout} className="btn-logout">
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
            <p className="stat-value">--</p>
            <p className="stat-label">Celkem v systému</p>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📞</div>
            <h3>Dnes volat</h3>
            <p className="stat-value">--</p>
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
            <span className="coming-soon">Připravujeme...</span>
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
              <h3>⚙️ Administrace</h3>
              <p>Správa systému a uživatelů</p>
              <ul>
                <li>Správa uživatelů</li>
                <li>Přehled provizí</li>
                <li>Nastavení balíčků</li>
              </ul>
              <span className="coming-soon">Připravujeme...</span>
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
