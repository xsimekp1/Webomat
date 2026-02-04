'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '../../../../context/AuthContext'
import { useToast } from '../../../../context/ToastContext'
import ApiClient from '../../../../lib/api'
import { getBackUrl } from '../../../../lib/navigation'

import './styles.css'

interface Project {
  id: string
  business_id: string
  package: string
  status: string
  price_setup: number | null
  price_monthly: number | null
  domain: string | null
  notes: string | null
  required_deadline: string | null
  budget: number | null
  domain_status: string | null
  internal_notes: string | null
  client_notes: string | null
  versions_count: number | null
  latest_version_id: string | null
  created_at: string | null
  updated_at: string | null
}

interface Version {
  id: string
  project_id: string
  version_number: number
  status: string
  notes: string | null
  html_content: string | null
  thumbnail_url: string | null
  screenshot_desktop_url: string | null
  public_url: string | null
  deployment_status: string | null
  is_current: boolean | null
  published_at: string | null
  created_at: string | null
}

interface ShareLink {
  id: string
  token: string
  preview_url: string
}

interface Invoice {
  id: string
  business_id: string
  project_id: string | null
  seller_id: string | null
  invoice_number: string
  issue_date: string
  due_date: string
  paid_date: string | null
  amount_without_vat: number
  vat_rate: number
  vat_amount: number | null
  amount_total: number
  currency: string
  payment_type: string
  status: string
  description: string | null
  variable_symbol: string | null
  created_at: string | null
  business_name: string | null
}

const STATUS_LABELS: Record<string, string> = {
  offer: 'Nabídka',
  interested: 'Zájem',
  in_progress: 'V práci',
  sent_for_review: 'K odeslání',
  revisions: 'Připomínky',
  invoiced: 'Fakturováno',
  closed: 'Uzavřeno',
  rejected: 'Zamítnuto',
  unpaid: 'Nezaplaceno',
  cancelled: 'Zrušeno',
}

const DOMAIN_STATUS_LABELS: Record<string, string> = {
  planned: 'Planovana',
  purchased: 'Zakoupena',
  deployed: 'Nasazena',
  not_needed: 'Neni potreba',
  other: 'Jina',
}

const DEPLOYMENT_STATUS_LABELS: Record<string, string> = {
  none: 'Nenasazeno',
  deploying: 'Nasazuje se...',
  deployed: 'Nasazeno',
  failed: 'Chyba',
  unpublished: 'Odebrano',
}

const INVOICE_STATUS_LABELS: Record<string, string> = {
  draft: 'Koncept',
  issued: 'Vystaveno',
  paid: 'Zaplaceno',
  overdue: 'Po splatnosti',
  cancelled: 'Zruseno',
}

const PAYMENT_TYPE_LABELS: Record<string, string> = {
  setup: 'Zrizeni',
  monthly: 'Mesicni',
  other: 'Jine',
}

export default function WebProjectPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const projectId = params.projectId as string

  const [project, setProject] = useState<Project | null>(null)
  const [versions, setVersions] = useState<Version[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'versions' | 'invoices' | 'settings'>('versions')

  // Action states
  const [deploying, setDeploying] = useState<string | null>(null)
  const [creatingLink, setCreatingLink] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [deletingProject, setDeletingProject] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null)
  const [showDeleteProjectModal, setShowDeleteProjectModal] = useState(false)
  const [shareLinks, setShareLinks] = useState<Record<string, ShareLink>>({})

  // Invoice states
  const [showInvoiceModal, setShowInvoiceModal] = useState(false)
  const [creatingInvoice, setCreatingInvoice] = useState(false)
  const [updatingInvoice, setUpdatingInvoice] = useState<string | null>(null)
  const [invoiceForm, setInvoiceForm] = useState({
    amount_without_vat: 0,
    payment_type: 'setup' as 'setup' | 'monthly' | 'other',
    description: '',
    vat_rate: 21,
    due_days: 14,
  })

  const loadProject = useCallback(async () => {
    try {
      setLoading(true)
      const [projectData, versionsData, invoicesData] = await Promise.all([
        ApiClient.getWebProject(projectId),
        ApiClient.getWebProjectVersions(projectId),
        ApiClient.getProjectInvoices(projectId),
      ])
      setProject(projectData)
      setVersions(versionsData.items || [])
      setInvoices(invoicesData || [])
      // Pre-fill invoice form with project price_setup
      if (projectData.price_setup) {
        setInvoiceForm(prev => ({ ...prev, amount_without_vat: projectData.price_setup }))
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodarilo se nacist projekt')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (projectId) {
      loadProject()
    }
  }, [projectId, loadProject])

  const handleDeploy = async (versionId: string) => {
    setDeploying(versionId)
    try {
      await ApiClient.deployVersion(versionId)
      await loadProject()
      showToast('Verze byla nasazena', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se nasadit verzi', 'error')
    } finally {
      setDeploying(null)
    }
  }

  const handleUndeploy = async (versionId: string) => {
    if (!confirm('Opravdu chcete odebrat nasazeni?')) return
    try {
      await ApiClient.undeployVersion(versionId)
      await loadProject()
      showToast('Nasazeni bylo odebrano', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se odebrat nasazeni', 'error')
    }
  }

  const handleCreateShareLink = async (versionId: string) => {
    setCreatingLink(versionId)
    try {
      const link = await ApiClient.createShareLink(versionId, { expires_in_days: 7 })
      setShareLinks(prev => ({ ...prev, [versionId]: link }))
      showToast('Odkaz pro sdileni byl vytvoren', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se vytvorit odkaz', 'error')
    } finally {
      setCreatingLink(null)
    }
  }

  const handleMarkAsCurrent = async (versionId: string) => {
    try {
      await ApiClient.markVersionAsCurrent(versionId)
      await loadProject()
      showToast('Verze byla nastavena jako aktualni', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se nastavit jako aktualni', 'error')
    }
  }

  const handleDeleteVersion = async (versionId: string) => {
    setDeleting(versionId)
    try {
      await ApiClient.deleteVersion(versionId)
      await loadProject()
      setShowDeleteModal(null)
      showToast('Verze byla smazana', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se smazat verzi', 'error')
    } finally {
      setDeleting(null)
    }
  }

  const handleDeleteProject = async () => {
    setDeletingProject(true)
    try {
      await ApiClient.deleteProject(projectId)
      setShowDeleteProjectModal(false)
      showToast('Projekt byl smazan', 'success')
      router.push('/dashboard')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se smazat projekt', 'error')
    } finally {
      setDeletingProject(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast('Odkaz byl zkopirovan do schranky', 'success')
  }

  const handleCreateInvoice = async () => {
    setCreatingInvoice(true)
    try {
      await ApiClient.generateProjectInvoice(projectId, {
        amount_without_vat: invoiceForm.amount_without_vat,
        payment_type: invoiceForm.payment_type,
        description: invoiceForm.description || undefined,
        vat_rate: invoiceForm.vat_rate,
        due_days: invoiceForm.due_days,
      })
      await loadProject()
      setShowInvoiceModal(false)
      showToast('Faktura byla vytvorena', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se vytvorit fakturu', 'error')
    } finally {
      setCreatingInvoice(false)
    }
  }

  const handleUpdateInvoiceStatus = async (invoiceId: string, newStatus: 'draft' | 'issued' | 'paid' | 'overdue' | 'cancelled') => {
    setUpdatingInvoice(invoiceId)
    try {
      await ApiClient.updateInvoiceStatus(invoiceId, {
        status: newStatus,
        paid_date: newStatus === 'paid' ? new Date().toISOString().split('T')[0] : undefined,
      })
      await loadProject()
      showToast(
        newStatus === 'paid'
          ? 'Faktura oznacena jako zaplacena - provize byla pripocitana'
          : 'Status faktury byl aktualizovan',
        'success'
      )
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se aktualizovat fakturu', 'error')
    } finally {
      setUpdatingInvoice(null)
    }
  }

  if (loading) {
    return (
      <div className="web-project-page">
        <div className="loading">Nacitam projekt...</div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="web-project-page">
        <div className="error-message">{error || 'Projekt nenalezen'}</div>
        <button onClick={() => router.push(getBackUrl(project?.business_id || ''))}>Zpet</button>
      </div>
    )
  }

  return (
    <div className="web-project-page">
      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.push(getBackUrl(project.business_id))}>
            ← Zpet
          </button>
          <div className="header-info">
            <h1>Sprava webu</h1>
            <div className="project-meta">
              <span className={`status-badge status-${project.status}`}>
                {STATUS_LABELS[project.status] || project.status}
              </span>
              <span className="package-badge">{project.package}</span>
              {project.domain && <span className="domain">{project.domain}</span>}
            </div>
          </div>
        </div>
        <button 
          className="btn-danger delete-project-btn" 
          onClick={() => setShowDeleteProjectModal(true)}
          disabled={deletingProject}
        >
          {deletingProject ? 'Mazání...' : 'Smazat projekt'}
        </button>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'versions' ? 'active' : ''}`}
          onClick={() => setActiveTab('versions')}
        >
          Verze ({versions.length})
        </button>
        <button
          className={`tab ${activeTab === 'invoices' ? 'active' : ''}`}
          onClick={() => setActiveTab('invoices')}
        >
          Faktury ({invoices.length})
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Nastaveni
        </button>
      </div>

      {/* Versions Tab */}
      {activeTab === 'versions' && (
        <div className="versions-section">
          {/* Generate new version button */}
          <div className="new-version-actions">
            <button
              className="btn-primary"
              onClick={() => router.push(`/dashboard/generate-website?projectId=${projectId}`)}
            >
              + Generovat novou verzi
            </button>
          </div>

          {/* Versions list */}
          {versions.length === 0 ? (
            <div className="empty-state">
              <p>Zatim zadne verze</p>
              <span>Vygenerujte prvni verzi webu</span>
            </div>
          ) : (
            <div className="versions-list">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className={`version-card ${version.is_current ? 'current' : ''}`}
                >
                  <div className="version-header">
                    <div className="version-info">
                      <span className="version-number">v{version.version_number}</span>
                      {version.is_current && (
                        <span className="current-badge">Aktualni</span>
                      )}
                      <span className={`deployment-badge deployment-${version.deployment_status || 'none'}`}>
                        {DEPLOYMENT_STATUS_LABELS[version.deployment_status || 'none']}
                      </span>
                    </div>
                    <span className="version-date">
                      {version.created_at
                        ? new Date(version.created_at).toLocaleDateString('cs-CZ')
                        : ''}
                    </span>
                  </div>

                  {/* Thumbnail */}
                  <div className="version-preview">
                    {version.thumbnail_url ? (
                      <img
                        src={version.thumbnail_url}
                        alt={`Verze ${version.version_number}`}
                        className="thumbnail"
                      />
                    ) : (
                      <div className="thumbnail-placeholder">
                        <span>Zadny nahled</span>
                      </div>
                    )}
                  </div>

                  {/* Notes */}
                  {version.notes && (
                    <div className="version-notes">
                      <p>{version.notes}</p>
                    </div>
                  )}

                  {/* Public URL */}
                  {version.public_url && (
                    <div className="version-url">
                      <a
                        href={version.public_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {version.public_url}
                      </a>
                    </div>
                  )}

                  {/* Share Link */}
                  {shareLinks[version.id] && (
                    <div className="share-link">
                      <input
                        type="text"
                        value={shareLinks[version.id].preview_url}
                        readOnly
                      />
                      <button
                        onClick={() => copyToClipboard(shareLinks[version.id].preview_url)}
                      >
                        Kopirovat
                      </button>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="version-actions">
                    {/* Preview HTML */}
                    {version.html_content && (
                      <button
                        className="btn-secondary"
                        onClick={() => {
                          const win = window.open('', '_blank')
                          if (win) {
                            win.document.write(version.html_content!)
                            win.document.close()
                          }
                        }}
                      >
                        Nahled
                      </button>
                    )}

                    {/* Deploy/Undeploy */}
                    {version.deployment_status === 'deployed' ? (
                      <button
                        className="btn-danger"
                        onClick={() => handleUndeploy(version.id)}
                      >
                        Odebrat
                      </button>
                    ) : (
                      <button
                        className="btn-primary"
                        onClick={() => handleDeploy(version.id)}
                        disabled={deploying === version.id || !version.html_content}
                      >
                        {deploying === version.id ? 'Nasazuje se...' : 'Nasadit'}
                      </button>
                    )}

                    {/* Share Link */}
                    <button
                      className="btn-secondary"
                      onClick={() => handleCreateShareLink(version.id)}
                      disabled={creatingLink === version.id}
                    >
                      {creatingLink === version.id ? 'Vytvari se...' : 'Sdilet'}
                    </button>

                    {/* Mark as Current */}
                    {!version.is_current && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleMarkAsCurrent(version.id)}
                      >
                        Nastavit jako aktualni
                      </button>
                    )}

                    {/* Delete */}
                    <button
                      className="btn-danger"
                      onClick={() => setShowDeleteModal(version.id)}
                      disabled={deleting === version.id}
                    >
                      Smazat
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Invoices Tab */}
      {activeTab === 'invoices' && (
        <div className="invoices-section">
          <div className="new-version-actions">
            <button
              className="btn-primary"
              onClick={() => setShowInvoiceModal(true)}
            >
              + Vystavit fakturu
            </button>
          </div>

          {invoices.length === 0 ? (
            <div className="empty-state">
              <p>Zatim zadne faktury</p>
              <span>Vystavte prvni fakturu pro tento projekt</span>
            </div>
          ) : (
            <div className="invoices-list">
              {invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className={`invoice-card invoice-status-${invoice.status}`}
                >
                  <div className="invoice-header">
                    <div className="invoice-info">
                      <span className="invoice-number">{invoice.invoice_number}</span>
                      <span className={`status-badge status-${invoice.status}`}>
                        {INVOICE_STATUS_LABELS[invoice.status] || invoice.status}
                      </span>
                      <span className="payment-type-badge">
                        {PAYMENT_TYPE_LABELS[invoice.payment_type] || invoice.payment_type}
                      </span>
                    </div>
                    <span className="invoice-amount">
                      {invoice.amount_total.toLocaleString('cs-CZ')} {invoice.currency}
                    </span>
                  </div>

                  <div className="invoice-details">
                    <div className="detail-row">
                      <span className="label">Castka bez DPH:</span>
                      <span>{invoice.amount_without_vat.toLocaleString('cs-CZ')} Kc</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">DPH ({invoice.vat_rate}%):</span>
                      <span>{(invoice.vat_amount || 0).toLocaleString('cs-CZ')} Kc</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Datum vystaveni:</span>
                      <span>{new Date(invoice.issue_date).toLocaleDateString('cs-CZ')}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Datum splatnosti:</span>
                      <span>{new Date(invoice.due_date).toLocaleDateString('cs-CZ')}</span>
                    </div>
                    {invoice.paid_date && (
                      <div className="detail-row">
                        <span className="label">Zaplaceno:</span>
                        <span>{new Date(invoice.paid_date).toLocaleDateString('cs-CZ')}</span>
                      </div>
                    )}
                    {invoice.variable_symbol && (
                      <div className="detail-row">
                        <span className="label">Var. symbol:</span>
                        <span>{invoice.variable_symbol}</span>
                      </div>
                    )}
                  </div>

                  {invoice.description && (
                    <div className="invoice-description">
                      <p>{invoice.description}</p>
                    </div>
                  )}

                  <div className="invoice-actions">
                    {invoice.status === 'draft' && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'issued')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        {updatingInvoice === invoice.id ? 'Aktualizuji...' : 'Vystavit'}
                      </button>
                    )}
                    {(invoice.status === 'issued' || invoice.status === 'overdue') && (
                      <button
                        className="btn-primary"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'paid')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        {updatingInvoice === invoice.id ? 'Aktualizuji...' : 'Oznacit jako zaplaceno'}
                      </button>
                    )}
                    {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                      <button
                        className="btn-danger"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'cancelled')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        Stornovat
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="settings-section">
          <div className="settings-card">
            <h3>Informace o projektu</h3>
            <div className="settings-grid">
              <div className="setting-item">
                <label>Balicek</label>
                <span>{project.package}</span>
              </div>
              <div className="setting-item">
                <label>Status</label>
                <span>{STATUS_LABELS[project.status] || project.status}</span>
              </div>
              <div className="setting-item">
                <label>Domena</label>
                <span>{project.domain || '-'}</span>
              </div>
              <div className="setting-item">
                <label>Stav domeny</label>
                <span>
                  {DOMAIN_STATUS_LABELS[project.domain_status || 'planned']}
                </span>
              </div>
              <div className="setting-item">
                <label>Cena setup</label>
                <span>
                  {project.price_setup
                    ? `${project.price_setup.toLocaleString('cs-CZ')} Kc`
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>Cena mesicne</label>
                <span>
                  {project.price_monthly
                    ? `${project.price_monthly.toLocaleString('cs-CZ')} Kc`
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>Deadline</label>
                <span>
                  {project.required_deadline
                    ? new Date(project.required_deadline).toLocaleDateString('cs-CZ')
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>Rozpocet</label>
                <span>
                  {project.budget
                    ? `${project.budget.toLocaleString('cs-CZ')} Kc`
                    : '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Notes */}
          {project.notes && (
            <div className="settings-card">
              <h3>Poznamky</h3>
              <p>{project.notes}</p>
            </div>
          )}

          {project.internal_notes && (
            <div className="settings-card">
              <h3>Interni poznamky</h3>
              <p>{project.internal_notes}</p>
            </div>
          )}

          {project.client_notes && (
            <div className="settings-card">
              <h3>Poznamky od klienta</h3>
              <p>{project.client_notes}</p>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Opravdu chcete smazat verzi?</h3>
            <p>Tato akce nelze vrátit zpět. Verze bude označena jako archivní.</p>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowDeleteModal(null)}
                disabled={deleting === showDeleteModal}
              >
                Zrusit
              </button>
              <button
                className="btn-danger"
                onClick={() => handleDeleteVersion(showDeleteModal)}
                disabled={deleting === showDeleteModal}
              >
                {deleting === showDeleteModal ? 'Mazani...' : 'Smazat'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Project Confirmation Modal */}
      {showDeleteProjectModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Opravdu chcete smazat celý projekt?</h3>
            <p>
              <strong>Upozornění:</strong> Tuto akci nelze vrátit zpět.
            </p>
            <ul className="modal-warnings">
              <li>Projekt bude trvale smazán (označen jako cancelled)</li>
              <li>Všechny verze budou archivovány</li>
              <li>Přiřazené faktury a komise zůstanou zachovány</li>
            </ul>
            <p>
              Pokud máte nasazené verze, nejdříve je musíte odstranit.
            </p>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowDeleteProjectModal(false)}
                disabled={deletingProject}
              >
                Zrušit
              </button>
              <button
                className="btn-danger"
                onClick={handleDeleteProject}
                disabled={deletingProject}
              >
                {deletingProject ? 'Mazání...' : 'Smazat projekt'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Invoice Modal */}
      {showInvoiceModal && (
        <div className="modal-overlay">
          <div className="modal invoice-modal">
            <h3>Vystavit fakturu</h3>
            <div className="invoice-form">
              <div className="form-group">
                <label>Castka bez DPH (Kc)</label>
                <input
                  type="number"
                  value={invoiceForm.amount_without_vat}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, amount_without_vat: parseFloat(e.target.value) || 0 })}
                  placeholder="0"
                />
              </div>

              <div className="form-group">
                <label>Typ platby</label>
                <select
                  value={invoiceForm.payment_type}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, payment_type: e.target.value as 'setup' | 'monthly' | 'other' })}
                >
                  <option value="setup">Zrizeni webu</option>
                  <option value="monthly">Mesicni provoz</option>
                  <option value="other">Jine</option>
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Sazba DPH (%)</label>
                  <input
                    type="number"
                    value={invoiceForm.vat_rate}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, vat_rate: parseFloat(e.target.value) || 21 })}
                  />
                </div>

                <div className="form-group">
                  <label>Splatnost (dni)</label>
                  <input
                    type="number"
                    value={invoiceForm.due_days}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, due_days: parseInt(e.target.value) || 14 })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Popis (nepovinne)</label>
                <textarea
                  value={invoiceForm.description}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, description: e.target.value })}
                  placeholder="Popis fakturovanych sluzeb..."
                  rows={3}
                />
              </div>

              <div className="invoice-preview">
                <div className="preview-row">
                  <span>Castka bez DPH:</span>
                  <span>{invoiceForm.amount_without_vat.toLocaleString('cs-CZ')} Kc</span>
                </div>
                <div className="preview-row">
                  <span>DPH ({invoiceForm.vat_rate}%):</span>
                  <span>{(invoiceForm.amount_without_vat * (invoiceForm.vat_rate / 100)).toLocaleString('cs-CZ')} Kc</span>
                </div>
                <div className="preview-row total">
                  <span>Celkem:</span>
                  <span>{(invoiceForm.amount_without_vat * (1 + invoiceForm.vat_rate / 100)).toLocaleString('cs-CZ')} Kc</span>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowInvoiceModal(false)}
                disabled={creatingInvoice}
              >
                Zrusit
              </button>
              <button
                className="btn-primary"
                onClick={handleCreateInvoice}
                disabled={creatingInvoice || invoiceForm.amount_without_vat <= 0}
              >
                {creatingInvoice ? 'Vytvarim...' : 'Vytvorit fakturu'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
