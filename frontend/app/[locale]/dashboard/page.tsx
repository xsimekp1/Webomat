'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { useLanguage } from '../../context/LanguageContext'
import { useTranslations } from 'next-intl'
import ApiClient from '../../lib/api'



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

function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const { showToast } = useToast()
  const { language } = useLanguage()
  const t = useTranslations('dashboard')
  console.log('Dashboard: Current language from LanguageContext:', language)

  // Seller dashboard data
  const [sellerData, setSellerData] = useState<SellerDashboard | null>(null)

  // Admin-only state
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null)
  const [generatorMode, setGeneratorMode] = useState<'dry_run' | 'ai'>('dry_run')
  const [testBusinessName, setTestBusinessName] = useState('Test Firma s.r.o.')
  const [testBusinessType, setTestBusinessType] = useState('restaurace')
  const [generating, setGenerating] = useState(false)
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null)
  const [deploying, setDeploying] = useState(false)
  const [deployedUrl, setDeployedUrl] = useState<string | null>(null)
  const [generatorError, setGeneratorError] = useState('')
  const [includeEnglish, setIncludeEnglish] = useState<'no' | 'auto' | 'client'>('no')
  
  // Reminder modal state
  const [showReminderModal, setShowReminderModal] = useState(false)
  const [reminderData, setReminderData] = useState<any>(null)
  const [error, setError] = useState('')

  // Auth check is handled by layout

  // Load seller dashboard data
  useEffect(() => {
    if (user && !authLoading) {
      ApiClient.getSellerDashboard()
        .then((data) => {
          console.log('Dashboard data loaded:', data)
          setSellerData(data)
        })
        .catch((err) => {
          console.error('Failed to load seller dashboard:', err)
        })
    }
  }, [user, authLoading])

  // Load admin stats
  useEffect(() => {
    if (user?.role === 'admin') {
      ApiClient.getAdminDashboardStats()
        .then(setAdminStats)
        .catch(() => {})
    }
  }, [user])

  const handleGenerateTest = async () => {
    setGenerating(true)
    setGeneratorError('')
    setGeneratedHtml(null)
    setDeployedUrl(null)

    try {
      const result = await ApiClient.generateTestWebsite({
        dry_run: generatorMode === 'dry_run',
        business_name: testBusinessName,
        business_type: testBusinessType,
        include_english: includeEnglish
      })
      setGeneratedHtml(result.html_content)
    } catch (err: any) {
      setGeneratorError(err.response?.data?.detail || 'Chyba při generování')
    } finally {
      setGenerating(false)
    }
  }

  const handleDeployTest = async () => {
    if (!generatedHtml) return

    setDeploying(true)
    setGeneratorError('')

    try {
      const result = await ApiClient.deployTestWebsite(generatedHtml, testBusinessName)
      setDeployedUrl(result.url)
    } catch (err: any) {
      setGeneratorError(err.response?.data?.detail || 'Chyba při nasazení')
    } finally {
      setDeploying(false)
    }
  }

  // Reminder generation
  const handleGenerateReminder = async (invoiceId: string) => {
    try {
      const reminder = await ApiClient.generatePaymentReminder(invoiceId)
      setShowReminderModal(true)
      setReminderData(reminder)
    } catch (err: any) {
      setError('Nepodařilo se vygenerovat upomínku')
    }
  }

  const handleSendReminder = async (invoiceId: string) => {
    try {
      await ApiClient.sendPaymentReminder(invoiceId)
      setShowReminderModal(false)
      setReminderData(null)
      ApiClient.getSellerDashboard()
        .then(setSellerData)
        .catch(() => {})
    } catch (err: any) {
      setError('Nepodařilo se odeslat upomínku')
    }
  }

  const handleToastTest = () => {
    showToast('TEST', 'success')
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
      offer: '#6b7280',
      in_production: '#3b82f6',
    }
    return colors[status] || '#6b7280'
  }

  const getProjectCardClass = (status: string) => {
    const classes: Record<string, string> = {
      offer: 'project-card-offer',
      in_production: 'project-card-in-production',
    }
    return classes[status] || 'project-card-default'
  }

  if (!user) {
    return null
  }

  return (
    <div className="dashboard-page">
        {/* Welcome + Quick Stats */}
        <div className="welcome-row">
          <h2>
            {t('greeting', { name: user.name?.split(' ')[0] || (language === 'cs' ? 'uživateli' : 'user') })}
            <span style={{ marginLeft: '8px' }}>
              {language === 'cs' ? '🇨🇿' : '🇬🇧'}
            </span>
          </h2>
        </div>

        {/* Quick Action Cards */}
        <div className="quick-stats-grid">
          <div className="quick-card balance-card" onClick={() => router.push('/dashboard/account')}>
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
              <span className="quick-card-label">Follow-upy</span>
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

        {/* Toast Test Button */}
        <div className="dashboard-section">
          <button 
            onClick={handleToastTest}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              marginBottom: '16px'
            }}
          >
            Toast Test
          </button>
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
                  className={`project-card ${getProjectCardClass(project.status)}`}
                  onClick={() => router.push(`/dashboard/web-project/${project.id}`)}
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
                  onClick={() => router.push(`/dashboard/invoices/${invoice.id}`)}
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
                  <button 
                    className="btn-reminder"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleGenerateReminder(invoice.id)
                    }}
                    title="Generovat upomínku"
                  >
                    📧
                  </button>
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
                    sandbox="allow-scripts allow-same-origin"
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
                    <button
                      onClick={handleDeployTest}
                      disabled={deploying}
                      className="btn-deploy"
                    >
                      {deploying ? 'Nasazuji...' : '🚀 Nasadit na web'}
                    </button>
                  </div>

                  {deployedUrl && (
                    <div className="deployed-url">
                      <p>✅ Web je dostupný na:</p>
                      <a href={deployedUrl} target="_blank" rel="noopener noreferrer">
                        {deployedUrl}
                      </a>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(deployedUrl)
                          showToast('URL zkopírována do schránky', 'success')
                        }}
                        className="btn-copy"
                      >
                        Kopírovat
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

      <style jsx>{`
        .dashboard-page {
          /* Page content styling */
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

        .btn-deploy {
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-deploy:hover {
          opacity: 0.9;
        }

        .btn-deploy:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .deployed-url {
          margin-top: 16px;
          padding: 16px;
          background: #dcfce7;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }

        .deployed-url p {
          margin: 0;
          color: #166534;
          font-weight: 500;
        }

        .deployed-url a {
          color: #15803d;
          word-break: break-all;
        }

        .btn-copy {
          padding: 6px 12px;
          border: 1px solid #22c55e;
          border-radius: 6px;
          background: white;
          color: #166534;
          cursor: pointer;
          font-size: 0.85rem;
        }

        .btn-copy:hover {
          background: #f0fdf4;
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

          .quick-card {
            padding: 16px;
            flex-direction: row;
            align-items: center;
          }

          .quick-card-icon {
            font-size: 1.5rem;
            margin-bottom: 0;
            margin-right: 12px;
          }

          .quick-card-value {
            font-size: 1.5rem;
          }

          .quick-card-label {
            font-size: 0.8rem;
            margin-top: 2px;
          }

          .quick-card-action {
            font-size: 0.75rem;
            margin-top: 0;
            margin-left: 12px;
            white-space: nowrap;
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

        .reminder-modal {
          max-width: 600px;
        }

        .reminder-info {
          display: grid;
          grid-template-columns: 120px 1fr;
          gap: 8px;
          margin-bottom: 20px;
        }

        .reminder-info .label {
          font-weight: 600;
          color: #475569;
        }

        .reminder-info .value {
          color: #1e293b;
        }

        .reminder-text {
          margin-top: 20px;
        }

        .reminder-text h4 {
          margin-bottom: 10px;
          color: #374151;
        }

        .reminder-text textarea {
          width: 100%;
          border: 1px solid #d1d5db;
          padding: 12px;
          border-radius: 8px;
          font-family: monospace;
          font-size: 13px;
          line-height: 1.4;
          resize: vertical;
        }

        .btn-reminder {
          background: #fbbf24;
          color: #78350f;
          border: none;
          padding: 6px 8px;
          border-radius: 4px;
          cursor: pointer;
          margin-left: 8px;
        }

        .btn-reminder:hover {
          background: #f59e0b;
        }
      `}</style>

      {/* Reminder Modal */}
      {showReminderModal && reminderData && (
        <div className="modal-overlay" onClick={() => setShowReminderModal(false)}>
          <div className="modal-content reminder-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📧 Upomínka na platbu</h3>
              <button className="modal-close" onClick={() => setShowReminderModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="reminder-info">
                <div className="info-row">
                  <span className="label">Klient:</span>
                  <span className="value">{reminderData.business_name}</span>
                </div>
                <div className="info-row">
                  <span className="label">Faktura:</span>
                  <span className="value">{reminderData.invoice_number}</span>
                </div>
                <div className="info-row">
                  <span className="label">Částka:</span>
                  <span className="value">{formatCurrency(reminderData.amount_total)}</span>
                </div>
                <div className="info-row">
                  <span className="label">Splatnost:</span>
                  <span className="value">{reminderData.due_date}</span>
                </div>
              </div>
              <div className="reminder-text">
                <h4>Text upomínky:</h4>
                <textarea
                  value={reminderData.reminder_text}
                  readOnly
                  rows={15}
                />
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowReminderModal(false)}>
                Zrušit
              </button>
              <button 
                className="btn-primary" 
                onClick={() => handleSendReminder(reminderData.invoice_id)}
              >
                Odeslat upomínku
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardPage
