'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import ApiClient from '../lib/api'

interface CRMStats {
  total_leads: number
  follow_ups_today: number
}

interface WeeklyInvoice {
  week_start: string
  week_end: string
  total_amount: number
  invoice_count: number
}

interface AdminStats {
  projects_in_production: number
  projects_delivered: number
  projects_won: number
  total_active_projects: number
  weekly_invoices: WeeklyInvoice[]
}

export default function DashboardPage() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState<CRMStats | null>(null)

  // Admin-only state
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null)
  const [generatorMode, setGeneratorMode] = useState<'dry_run' | 'ai'>('dry_run')
  const [testBusinessName, setTestBusinessName] = useState('Test Firma s.r.o.')
  const [testBusinessType, setTestBusinessType] = useState('restaurace')
  const [generating, setGenerating] = useState(false)
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null)
  const [generatorError, setGeneratorError] = useState('')

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

  // Load admin stats
  useEffect(() => {
    if (isAuthenticated && user?.role === 'admin') {
      ApiClient.getAdminDashboardStats()
        .then(setAdminStats)
        .catch(() => {})
    }
  }, [isAuthenticated, user])

  const handleGenerateTest = async () => {
    setGenerating(true)
    setGeneratorError('')
    setGeneratedHtml(null)

    try {
      const result = await ApiClient.generateTestWebsite(
        generatorMode === 'dry_run',
        testBusinessName,
        testBusinessType
      )
      setGeneratedHtml(result.html_content)
    } catch (err: any) {
      setGeneratorError(err.response?.data?.detail || 'Chyba při generování')
    } finally {
      setGenerating(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('cs-CZ', {
      style: 'currency',
      currency: 'CZK',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatWeekLabel = (weekStart: string) => {
    const date = new Date(weekStart)
    return `${date.getDate()}.${date.getMonth() + 1}.`
  }

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

        {/* Admin-only: Rozšířené statistiky a nástroje */}
        {user.role === 'admin' && (
          <div className="admin-section">
            <h2>Admin Dashboard</h2>

            {/* Statistiky projektů */}
            <div className="admin-stats-grid">
              <div className="admin-stat-card">
                <div className="stat-icon">🏆</div>
                <h3>Vyhráno</h3>
                <p className="stat-value">{adminStats?.projects_won ?? '--'}</p>
                <p className="stat-label">Čeká na výrobu</p>
              </div>
              <div className="admin-stat-card">
                <div className="stat-icon">🔧</div>
                <h3>Ve výrobě</h3>
                <p className="stat-value">{adminStats?.projects_in_production ?? '--'}</p>
                <p className="stat-label">Rozpracováno</p>
              </div>
              <div className="admin-stat-card">
                <div className="stat-icon">✅</div>
                <h3>Dodáno</h3>
                <p className="stat-value">{adminStats?.projects_delivered ?? '--'}</p>
                <p className="stat-label">K nasazení</p>
              </div>
              <div className="admin-stat-card highlight">
                <div className="stat-icon">📊</div>
                <h3>Celkem aktivních</h3>
                <p className="stat-value">{adminStats?.total_active_projects ?? '--'}</p>
                <p className="stat-label">Projektů</p>
              </div>
            </div>

            {/* Graf týdenní fakturace */}
            <div className="invoice-chart-section">
              <h3>Týdenní fakturace (3 měsíce)</h3>
              {adminStats?.weekly_invoices && adminStats.weekly_invoices.length > 0 ? (
                <div className="chart-container">
                  <div className="bar-chart">
                    {adminStats.weekly_invoices.map((week, index) => {
                      const maxAmount = Math.max(...adminStats.weekly_invoices.map(w => w.total_amount), 1)
                      const heightPercent = (week.total_amount / maxAmount) * 100
                      return (
                        <div key={index} className="bar-wrapper">
                          <div
                            className="bar"
                            style={{ height: `${Math.max(heightPercent, 2)}%` }}
                            title={`${formatWeekLabel(week.week_start)}: ${formatCurrency(week.total_amount)} (${week.invoice_count} faktur)`}
                          >
                            {week.total_amount > 0 && (
                              <span className="bar-value">{Math.round(week.total_amount / 1000)}k</span>
                            )}
                          </div>
                          <span className="bar-label">{formatWeekLabel(week.week_start)}</span>
                        </div>
                      )
                    })}
                  </div>
                  <div className="chart-summary">
                    Celkem za období: {formatCurrency(adminStats.weekly_invoices.reduce((sum, w) => sum + w.total_amount, 0))}
                  </div>
                </div>
              ) : (
                <p className="no-data">Žádná data o fakturaci</p>
              )}
            </div>

            {/* Generátor testovacího webu */}
            <div className="test-generator-section">
              <h3>🧪 Generátor testovacího webu</h3>
              <p>Rychlé vygenerování testovací stránky bez nutnosti vytvářet projekt</p>

              <div className="generator-form">
                <div className="form-row">
                  <div className="form-field">
                    <label>Název firmy</label>
                    <input
                      type="text"
                      value={testBusinessName}
                      onChange={(e) => setTestBusinessName(e.target.value)}
                      placeholder="Test Firma s.r.o."
                    />
                  </div>
                  <div className="form-field">
                    <label>Typ podnikání</label>
                    <input
                      type="text"
                      value={testBusinessType}
                      onChange={(e) => setTestBusinessType(e.target.value)}
                      placeholder="restaurace"
                    />
                  </div>
                </div>

                <div className="mode-selector">
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="generatorMode"
                      checked={generatorMode === 'dry_run'}
                      onChange={() => setGeneratorMode('dry_run')}
                    />
                    <span className="radio-label">
                      <strong>DRY RUN</strong>
                      <small>Testovací HTML bez AI (zdarma)</small>
                    </span>
                  </label>
                  <label className="radio-option disabled">
                    <input
                      type="radio"
                      name="generatorMode"
                      checked={generatorMode === 'ai'}
                      onChange={() => setGeneratorMode('ai')}
                      disabled
                    />
                    <span className="radio-label">
                      <strong>AI Generování</strong>
                      <small>Claude API (připravujeme...)</small>
                    </span>
                  </label>
                </div>

                <button
                  onClick={handleGenerateTest}
                  disabled={generating}
                  className="btn-generate"
                >
                  {generating ? 'Generuji...' : 'Vygenerovat testovací web'}
                </button>

                {generatorError && (
                  <div className="generator-error">{generatorError}</div>
                )}
              </div>

              {generatedHtml && (
                <div className="generated-preview">
                  <h4>Náhled vygenerovaného webu:</h4>
                  <iframe
                    srcDoc={generatedHtml}
                    className="preview-iframe"
                    title="Preview"
                  />
                  <div className="preview-actions">
                    <button
                      onClick={() => {
                        const blob = new Blob([generatedHtml], { type: 'text/html' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = 'test-web.html'
                        a.click()
                        URL.revokeObjectURL(url)
                      }}
                      className="btn-download"
                    >
                      Stáhnout HTML
                    </button>
                    <button
                      onClick={() => {
                        const win = window.open('', '_blank')
                        win?.document.write(generatedHtml)
                      }}
                      className="btn-fullscreen"
                    >
                      Otevřít v novém okně
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
