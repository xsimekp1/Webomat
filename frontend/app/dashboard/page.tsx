'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import ApiClient from '../lib/api'

interface SellerDashboard {
  available_balance: number
  pending_projects_amount: number
  recent_invoices: any[]
  weekly_rewards: any[]
  pending_projects: PendingProject[]
  unpaid_client_invoices: UnpaidInvoice[]
  total_leads: number
  follow_ups_today: number
}

interface PendingProject {
  id: string
  business_id: string
  business_name: string
  status: string
  package: string
  latest_version_number: number | null
  latest_version_date: string | null
}

interface UnpaidInvoice {
  id: string
  business_id: string
  business_name: string
  invoice_number: string
  amount_total: number
  due_date: string
  days_overdue: number
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

  // Seller dashboard data
  const [sellerData, setSellerData] = useState<SellerDashboard | null>(null)

  // Admin-only state
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null)
  const [generatorMode, setGeneratorMode] = useState<'dry_run' | 'ai'>('dry_run')
  const [testBusinessName, setTestBusinessName] = useState('Test Firma s.r.o.')
  const [testBusinessType, setTestBusinessType] = useState('restaurace')
  const [generating, setGenerating] = useState(false)
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null)
  const [generatorError, setGeneratorError] = useState('')
  const [includeEnglish, setIncludeEnglish] = useState<'no' | 'auto' | 'client'>('no')

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isLoading, isAuthenticated, router])

  // Load seller dashboard data
  useEffect(() => {
    if (isAuthenticated) {
      ApiClient.getSellerDashboard()
        .then(setSellerData)
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
        testBusinessType,
        includeEnglish
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

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return `${date.getDate()}.${date.getMonth() + 1}.${date.getFullYear()}`
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      won: 'Vyhráno',
      in_production: 'Ve výrobě',
      delivered: 'Dodáno',
      offer: 'Nabídka',
      live: 'Živé',
    }
    return labels[status] || status
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      won: '#f59e0b',
      in_production: '#3b82f6',
      delivered: '#10b981',
      offer: '#6b7280',
    }
    return colors[status] || '#6b7280'
  }

  if (isLoading || !user) {
    return <div className="loading">Načítám...</div>
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Webomat</h1>
        </div>
        <div className="header-right">
          <span className="user-info">
            {user.name} <span className="role-badge">{user.role === 'admin' ? 'Admin' : 'Obchodník'}</span>
          </span>
          <button onClick={() => router.push('/help')} className="btn-icon" title="Nápověda">
            ?
          </button>
          <button onClick={() => router.push('/dashboard/profile')} className="btn-icon" title="Můj profil">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </button>
          <button onClick={logout} className="btn-logout">
            Odhlásit
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Welcome + Quick Stats */}
        <div className="welcome-row">
          <h2>Ahoj, {user.name?.split(' ')[0] || 'uživateli'}!</h2>
        </div>

        {/* Quick Action Cards */}
        <div className="quick-stats-grid">
          <div className="quick-card balance-card" onClick={() => router.push('/dashboard/profile')}>
            <div className="quick-card-icon">💰</div>
            <div className="quick-card-content">
              <span className="quick-card-value">{formatCurrency(sellerData?.available_balance || 0)}</span>
              <span className="quick-card-label">K vyplacení</span>
            </div>
            <div className="quick-card-action">Detail účtu →</div>
          </div>

          <div className="quick-card calls-card" onClick={() => router.push('/dashboard/crm?filter=followup')}>
            <div className="quick-card-icon">📞</div>
            <div className="quick-card-content">
              <span className="quick-card-value">{sellerData?.follow_ups_today ?? '--'}</span>
              <span className="quick-card-label">Dnes volat</span>
            </div>
            <div className="quick-card-action">Otevřít seznam →</div>
          </div>

          <div className="quick-card leads-card" onClick={() => router.push('/dashboard/crm')}>
            <div className="quick-card-icon">📊</div>
            <div className="quick-card-content">
              <span className="quick-card-value">{sellerData?.total_leads ?? '--'}</span>
              <span className="quick-card-label">Moje leady</span>
            </div>
            <div className="quick-card-action">Jít do CRM →</div>
          </div>
        </div>

        {/* Pending Projects */}
        {sellerData?.pending_projects && sellerData.pending_projects.length > 0 && (
          <section className="dashboard-section">
            <div className="section-header">
              <h3>🔧 Rozpracované projekty ({sellerData.pending_projects.length})</h3>
              <button className="btn-link" onClick={() => router.push('/dashboard/crm?filter=projects')}>
                Zobrazit vše
              </button>
            </div>
            <div className="projects-scroll">
              {sellerData.pending_projects.slice(0, 5).map((project) => (
                <div
                  key={project.id}
                  className="project-card"
                  onClick={() => router.push(`/dashboard/crm/${project.business_id}`)}
                >
                  <div className="project-name">{project.business_name}</div>
                  <div className="project-status" style={{ color: getStatusColor(project.status) }}>
                    ● {getStatusLabel(project.status)}
                  </div>
                  <div className="project-version">
                    {project.latest_version_number
                      ? `v${project.latest_version_number}`
                      : 'Bez verze'}
                    {project.latest_version_date && (
                      <span className="version-date"> · {formatDate(project.latest_version_date)}</span>
                    )}
                  </div>
                  <div className="project-package">{project.package}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Empty state for projects */}
        {(!sellerData?.pending_projects || sellerData.pending_projects.length === 0) && (
          <section className="dashboard-section">
            <div className="section-header">
              <h3>🔧 Rozpracované projekty</h3>
            </div>
            <div className="empty-state">
              <p>Zatím nemáte žádné rozpracované projekty.</p>
              <small style={{ display: 'block', marginTop: '8px', color: '#94a3b8' }}>
                Po uzavření dealu vytvořte projekt a objeví se zde
              </small>
              <button className="btn-primary" onClick={() => router.push('/dashboard/crm')}>
                Přidat nový lead
              </button>
            </div>
          </section>
        )}

        {/* Unpaid Invoices */}
        {sellerData?.unpaid_client_invoices && sellerData.unpaid_client_invoices.length > 0 && (
          <section className="dashboard-section warning-section">
            <div className="section-header">
              <h3>⚠️ Nezaplacené faktury od klientů ({sellerData.unpaid_client_invoices.length})</h3>
            </div>
            <div className="invoices-table">
              {sellerData.unpaid_client_invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className={`invoice-row ${invoice.days_overdue > 0 ? 'overdue' : ''}`}
                  onClick={() => router.push(`/dashboard/crm/${invoice.business_id}`)}
                >
                  <div className="invoice-business">{invoice.business_name}</div>
                  <div className="invoice-number">{invoice.invoice_number}</div>
                  <div className="invoice-amount">{formatCurrency(invoice.amount_total)}</div>
                  <div className="invoice-status">
                    {invoice.days_overdue > 0 ? (
                      <span className="status-overdue">{invoice.days_overdue} dní po splatnosti</span>
                    ) : invoice.days_overdue === 0 ? (
                      <span className="status-today">Splatnost dnes</span>
                    ) : (
                      <span className="status-upcoming">za {Math.abs(invoice.days_overdue)} dní</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Quick Actions */}
        <section className="quick-actions">
          <button className="action-btn primary" onClick={() => router.push('/dashboard/crm?action=new')}>
            + Nový lead
          </button>
          {user.role === 'admin' && (
            <button className="action-btn" onClick={() => router.push('/dashboard/admin')}>
              👥 Správa uživatelů
            </button>
          )}
        </section>

        {/* Admin Section */}
        {user.role === 'admin' && (
          <div className="admin-section">
            <h2>Admin Dashboard</h2>

            {/* Admin Stats Grid */}
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

            {/* Weekly Invoice Chart */}
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

            {/* Test Generator */}
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

                {/* English Version */}
                <div className="language-selector">
                  <label className="section-label">Anglická verze webu</label>
                  <div className="mode-selector">
                    <label className="radio-option">
                      <input
                        type="radio"
                        name="includeEnglish"
                        checked={includeEnglish === 'no'}
                        onChange={() => setIncludeEnglish('no')}
                      />
                      <span className="radio-label">
                        <strong>Ne</strong>
                        <small>Pouze česká verze</small>
                      </span>
                    </label>
                    <label className="radio-option">
                      <input
                        type="radio"
                        name="includeEnglish"
                        checked={includeEnglish === 'auto'}
                        onChange={() => setIncludeEnglish('auto')}
                      />
                      <span className="radio-label">
                        <strong>Automaticky</strong>
                        <small>Přeložit pomocí AI</small>
                      </span>
                    </label>
                    <label className="radio-option">
                      <input
                        type="radio"
                        name="includeEnglish"
                        checked={includeEnglish === 'client'}
                        onChange={() => setIncludeEnglish('client')}
                      />
                      <span className="radio-label">
                        <strong>Od klienta</strong>
                        <small>Klient dodá texty</small>
                      </span>
                    </label>
                  </div>
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

      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: #f8fafc;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: white;
          border-bottom: 1px solid #e2e8f0;
          position: sticky;
          top: 0;
          z-index: 100;
        }

        .header-left h1 {
          font-size: 1.5rem;
          font-weight: 700;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .user-info {
          font-size: 0.9rem;
          color: #64748b;
        }

        .role-badge {
          background: #f1f5f9;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.75rem;
          margin-left: 4px;
        }

        .btn-icon {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border: 1px solid #e2e8f0;
          background: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: #f8fafc;
          border-color: #cbd5e1;
        }

        .btn-logout {
          padding: 8px 16px;
          background: #fee2e2;
          color: #dc2626;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-logout:hover {
          background: #fecaca;
        }

        .dashboard-main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        .welcome-row {
          margin-bottom: 24px;
        }

        .welcome-row h2 {
          font-size: 1.75rem;
          font-weight: 600;
          color: #1e293b;
          margin: 0;
        }

        /* Quick Stats Cards */
        .quick-stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .quick-card {
          background: white;
          border-radius: 16px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #e2e8f0;
        }

        .quick-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }

        .balance-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .calls-card {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          color: white;
          border: none;
        }

        .leads-card {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          border: none;
        }

        .quick-card-icon {
          font-size: 2rem;
          margin-bottom: 12px;
        }

        .quick-card-content {
          flex: 1;
        }

        .quick-card-value {
          display: block;
          font-size: 2rem;
          font-weight: 700;
          line-height: 1.2;
        }

        .quick-card-label {
          display: block;
          font-size: 0.9rem;
          opacity: 0.9;
          margin-top: 4px;
        }

        .quick-card-action {
          margin-top: 16px;
          font-size: 0.85rem;
          opacity: 0.8;
          font-weight: 500;
        }

        /* Dashboard Sections */
        .dashboard-section {
          background: white;
          border-radius: 16px;
          padding: 20px;
          margin-bottom: 24px;
          border: 1px solid #e2e8f0;
        }

        .warning-section {
          border-color: #fbbf24;
          background: #fffbeb;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .section-header h3 {
          font-size: 1.1rem;
          font-weight: 600;
          color: #1e293b;
          margin: 0;
        }

        .btn-link {
          background: none;
          border: none;
          color: #667eea;
          cursor: pointer;
          font-size: 0.9rem;
          font-weight: 500;
        }

        .btn-link:hover {
          text-decoration: underline;
        }

        /* Projects Scroll */
        .projects-scroll {
          display: flex;
          gap: 16px;
          overflow-x: auto;
          padding-bottom: 8px;
        }

        .project-card {
          flex: 0 0 220px;
          background: #f8fafc;
          border-radius: 12px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #e2e8f0;
        }

        .project-card:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
        }

        .project-name {
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 8px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .project-status {
          font-size: 0.85rem;
          font-weight: 500;
          margin-bottom: 8px;
        }

        .project-version {
          font-size: 0.8rem;
          color: #64748b;
        }

        .version-date {
          color: #94a3b8;
        }

        .project-package {
          margin-top: 8px;
          font-size: 0.75rem;
          text-transform: uppercase;
          color: #94a3b8;
          letter-spacing: 0.5px;
        }

        /* Invoices Table */
        .invoices-table {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .invoice-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1.5fr;
          gap: 16px;
          padding: 12px 16px;
          background: white;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          align-items: center;
        }

        .invoice-row:hover {
          background: #fef3c7;
        }

        .invoice-row.overdue {
          border-left: 3px solid #dc2626;
        }

        .invoice-business {
          font-weight: 500;
          color: #1e293b;
        }

        .invoice-number {
          color: #64748b;
          font-size: 0.9rem;
        }

        .invoice-amount {
          font-weight: 600;
          color: #1e293b;
        }

        .status-overdue {
          color: #dc2626;
          font-weight: 500;
          font-size: 0.85rem;
        }

        .status-today {
          color: #f59e0b;
          font-weight: 500;
          font-size: 0.85rem;
        }

        .status-upcoming {
          color: #64748b;
          font-size: 0.85rem;
        }

        /* Empty State */
        .empty-state {
          text-align: center;
          padding: 32px;
          color: #64748b;
        }

        .empty-state p {
          margin-bottom: 16px;
        }

        /* Quick Actions */
        .quick-actions {
          display: flex;
          gap: 12px;
          margin-bottom: 32px;
        }

        .action-btn {
          padding: 12px 24px;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
          background: white;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: #f8fafc;
        }

        .action-btn.primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .action-btn.primary:hover {
          opacity: 0.9;
        }

        .btn-primary {
          padding: 10px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        /* Admin Section */
        .admin-section {
          margin-top: 48px;
          padding-top: 32px;
          border-top: 2px solid #e2e8f0;
        }

        .admin-section h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 24px;
          color: #1e293b;
        }

        .admin-stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .admin-stat-card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          text-align: center;
          border: 1px solid #e2e8f0;
        }

        .admin-stat-card.highlight {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .admin-stat-card .stat-icon {
          font-size: 2rem;
          margin-bottom: 8px;
        }

        .admin-stat-card h3 {
          font-size: 0.9rem;
          font-weight: 500;
          margin: 0 0 8px 0;
          opacity: 0.8;
        }

        .admin-stat-card .stat-value {
          font-size: 2rem;
          font-weight: 700;
          margin: 0;
        }

        .admin-stat-card .stat-label {
          font-size: 0.8rem;
          opacity: 0.7;
          margin: 4px 0 0 0;
        }

        /* Chart */
        .invoice-chart-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 24px;
          border: 1px solid #e2e8f0;
        }

        .invoice-chart-section h3 {
          margin: 0 0 20px 0;
          font-size: 1.1rem;
        }

        .chart-container {
          padding: 16px 0;
        }

        .bar-chart {
          display: flex;
          align-items: flex-end;
          height: 200px;
          gap: 4px;
        }

        .bar-wrapper {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
        }

        .bar {
          width: 100%;
          background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
          border-radius: 4px 4px 0 0;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          min-height: 4px;
          transition: height 0.3s;
        }

        .bar-value {
          color: white;
          font-size: 0.7rem;
          font-weight: 600;
          padding-top: 4px;
        }

        .bar-label {
          font-size: 0.7rem;
          color: #64748b;
          margin-top: 8px;
        }

        .chart-summary {
          text-align: center;
          margin-top: 16px;
          color: #64748b;
          font-size: 0.9rem;
        }

        .no-data {
          color: #94a3b8;
          text-align: center;
          padding: 32px;
        }

        /* Generator */
        .test-generator-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          border: 1px solid #e2e8f0;
        }

        .test-generator-section h3 {
          margin: 0 0 8px 0;
        }

        .test-generator-section > p {
          color: #64748b;
          margin: 0 0 20px 0;
        }

        .generator-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        .form-field label {
          display: block;
          font-size: 0.85rem;
          font-weight: 500;
          margin-bottom: 6px;
          color: #374151;
        }

        .form-field input {
          width: 100%;
          padding: 10px 14px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 0.95rem;
        }

        .form-field input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .section-label {
          font-size: 0.85rem;
          font-weight: 500;
          color: #374151;
          margin-bottom: 8px;
          display: block;
        }

        .mode-selector {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .radio-option {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 12px 16px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          flex: 1;
          min-width: 150px;
          transition: all 0.2s;
        }

        .radio-option:hover {
          border-color: #667eea;
        }

        .radio-option.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .radio-option input[type="radio"] {
          margin-top: 2px;
        }

        .radio-label {
          display: flex;
          flex-direction: column;
        }

        .radio-label strong {
          font-size: 0.9rem;
        }

        .radio-label small {
          font-size: 0.75rem;
          color: #6b7280;
          margin-top: 2px;
        }

        .language-selector {
          margin-top: 8px;
        }

        .btn-generate {
          padding: 12px 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-generate:hover {
          opacity: 0.9;
        }

        .btn-generate:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .generator-error {
          color: #dc2626;
          background: #fef2f2;
          padding: 12px;
          border-radius: 8px;
          font-size: 0.9rem;
        }

        .generated-preview {
          margin-top: 24px;
          padding-top: 24px;
          border-top: 1px solid #e5e7eb;
        }

        .generated-preview h4 {
          margin: 0 0 16px 0;
        }

        .preview-iframe {
          width: 100%;
          height: 400px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
        }

        .preview-actions {
          display: flex;
          gap: 12px;
          margin-top: 16px;
        }

        .btn-download, .btn-fullscreen {
          padding: 10px 20px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-download:hover, .btn-fullscreen:hover {
          background: #f9fafb;
        }

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          font-size: 1.1rem;
          color: #64748b;
        }

        @media (max-width: 768px) {
          .dashboard-header {
            padding: 12px 16px;
          }

          .dashboard-main {
            padding: 16px;
          }

          .quick-stats-grid {
            grid-template-columns: 1fr;
          }

          .form-row {
            grid-template-columns: 1fr;
          }

          .invoice-row {
            grid-template-columns: 1fr;
            gap: 8px;
          }

          .mode-selector {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  )
}
