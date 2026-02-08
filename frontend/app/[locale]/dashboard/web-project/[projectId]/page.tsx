'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
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

export default function WebProjectPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const t = useTranslations('webProject')
  const tc = useTranslations('common')
  const projectId = params.projectId as string
  const locale = (params.locale as string) || 'cs'

  const getStatusLabel = (status: string) => {
    const map: Record<string, string> = {
      offer: t('statusOffer'), interested: t('statusInterested'), in_progress: t('statusInProgress'),
      sent_for_review: t('statusSentForReview'), revisions: t('statusRevisions'), invoiced: t('statusInvoiced'),
      closed: t('statusClosed'), rejected: t('statusRejected'), unpaid: t('statusUnpaid'), cancelled: t('statusCancelled'),
    }
    return map[status] || status
  }

  const getDomainStatusLabel = (status: string) => {
    const map: Record<string, string> = {
      planned: t('domainPlanned'), purchased: t('domainPurchased'), deployed: t('domainDeployed'),
      not_needed: t('domainNotNeeded'), other: t('domainOther'),
    }
    return map[status] || status
  }

  const getDeploymentStatusLabel = (status: string) => {
    const map: Record<string, string> = {
      none: t('deployNone'), deploying: t('deployDeploying'), deployed: t('deployDeployed'),
      failed: t('deployFail'), unpublished: t('deployUnpublished'),
    }
    return map[status] || status
  }

  const getInvoiceStatusLabel = (status: string) => {
    const map: Record<string, string> = {
      draft: t('invoiceDraft'), issued: t('invoiceIssued'), paid: t('invoicePaid'),
      overdue: t('invoiceOverdue'), cancelled: t('invoiceCancelled'),
    }
    return map[status] || status
  }

  const getPaymentTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      setup: t('paymentTypeSetup'), monthly: t('paymentTypeMonthly'), other: t('paymentTypeOther'),
    }
    return map[type] || type
  }

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
  const [generatingPdf, setGeneratingPdf] = useState<string | null>(null)
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
      setError(err.response?.data?.detail || t('loadError'))
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
      showToast(t('versionDeployed'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('deployFailed'), 'error')
    } finally {
      setDeploying(null)
    }
  }

  const handleUndeploy = async (versionId: string) => {
    if (!confirm(t('undeployConfirm'))) return
    try {
      await ApiClient.undeployVersion(versionId)
      await loadProject()
      showToast(t('undeploySuccess'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('undeployFailed'), 'error')
    }
  }

  const handleCreateShareLink = async (versionId: string) => {
    setCreatingLink(versionId)
    try {
      const link = await ApiClient.createShareLink(versionId, { expires_in_days: 7 })
      setShareLinks(prev => ({ ...prev, [versionId]: link }))
      showToast(t('shareLinkCreated'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('shareLinkFailed'), 'error')
    } finally {
      setCreatingLink(null)
    }
  }

  const handleMarkAsCurrent = async (versionId: string) => {
    try {
      await ApiClient.markVersionAsCurrent(versionId)
      await loadProject()
      showToast(t('currentSet'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('currentSetFailed'), 'error')
    }
  }

const handleDeleteVersion = async (versionId: string) => {
    setDeleting(versionId)
    try {
      await ApiClient.deleteVersion(versionId)
      setShowDeleteModal(null) // Close modal immediately
      await loadProject() // Reload data in background
      showToast(t('versionDeleted'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('versionDeleteFailed'), 'error')
      setShowDeleteModal(null) // Close modal even on error
    } finally {
      setDeleting(null)
    }
  }

  const handleDeleteProject = async () => {
    setDeletingProject(true)
    try {
      await ApiClient.deleteProject(projectId)
      setShowDeleteProjectModal(false)
      showToast(t('projectDeleted'), 'success')
      router.push('/dashboard')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('projectDeleteFailed'), 'error')
    } finally {
      setDeletingProject(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast(t('linkCopied'), 'success')
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
      showToast(t('invoiceCreated'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('invoiceCreateFailed'), 'error')
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
          ? t('invoicePaidCommission')
          : t('invoiceStatusUpdated'),
        'success'
      )
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('invoiceUpdateFailed'), 'error')
    } finally {
      setUpdatingInvoice(null)
    }
  }

  const handleGenerateAndDownloadPdf = async (invoiceId: string) => {
    setGeneratingPdf(invoiceId)
    try {
      const result = await ApiClient.generateInvoicePdf(invoiceId)
      if (result.pdf_url) {
        window.open(result.pdf_url, '_blank')
        showToast(t('pdfGenerated'), 'success')
      }
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('pdfGenerateFailed'), 'error')
    } finally {
      setGeneratingPdf(null)
    }
  }

  if (loading) {
    return (
      <div className="web-project-page">
        <div className="loading">{t('loading')}</div>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="web-project-page">
        <div className="error-message">{error || t('notFound')}</div>
        <button onClick={() => router.push(getBackUrl(project?.business_id || ''))}>{t('backButton')}</button>
      </div>
    )
  }

  return (
    <div className="web-project-page">
      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.push(getBackUrl(project.business_id))}>
            {t('backButton')}
          </button>
          <div className="header-info">
            <h1>{t('title')}</h1>
            <div className="project-meta">
              <span className={`status-badge status-${project.status}`}>
                {getStatusLabel(project.status)}
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
          {deletingProject ? t('deletingProject') : t('deleteProject')}
        </button>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'versions' ? 'active' : ''}`}
          onClick={() => setActiveTab('versions')}
        >
          {t('versionsTab', { count: versions.length })}
        </button>
        <button
          className={`tab ${activeTab === 'invoices' ? 'active' : ''}`}
          onClick={() => setActiveTab('invoices')}
        >
          {t('invoicesTab', { count: invoices.length })}
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          {t('settingsTab')}
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
              {t('generateNewVersion')}
            </button>
          </div>

          {/* Versions list */}
          {versions.length === 0 ? (
            <div className="empty-state">
              <p>{t('noVersions')}</p>
              <span>{t('generateFirstVersion')}</span>
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
                        <span className="current-badge">{t('current')}</span>
                      )}
                      <span className={`deployment-badge deployment-${version.deployment_status || 'none'}`}>
                        {getDeploymentStatusLabel(version.deployment_status || 'none')}
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
                        <span>{t('noPreview')}</span>
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
                        {t('copyLink')}
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
                        {t('preview')}
                      </button>
                    )}

                    {/* Deploy/Undeploy */}
                    {version.deployment_status === 'deployed' ? (
                      <button
                        className="btn-danger"
                        onClick={() => handleUndeploy(version.id)}
                      >
                        {t('undeploy')}
                      </button>
                    ) : (
                      <button
                        className="btn-primary"
                        onClick={() => handleDeploy(version.id)}
                        disabled={deploying === version.id || !version.html_content}
                      >
                        {deploying === version.id ? t('deploying') : t('deploy')}
                      </button>
                    )}

                    {/* Share Link */}
                    <button
                      className="btn-secondary"
                      onClick={() => handleCreateShareLink(version.id)}
                      disabled={creatingLink === version.id}
                    >
                      {creatingLink === version.id ? t('creatingLink') : t('share')}
                    </button>

                    {/* Mark as Current */}
                    {!version.is_current && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleMarkAsCurrent(version.id)}
                      >
                        {t('setAsCurrent')}
                      </button>
                    )}

                    {/* Delete */}
                    <button
                      className="btn-danger"
                      onClick={() => setShowDeleteModal(version.id)}
                      disabled={deleting === version.id}
                    >
                      {tc('delete')}
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
              {t('createInvoice')}
            </button>
          </div>

          {invoices.length === 0 ? (
            <div className="empty-state">
              <p>{t('noInvoices')}</p>
              <span>{t('createFirstInvoice')}</span>
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
                        {getInvoiceStatusLabel(invoice.status)}
                      </span>
                      <span className="payment-type-badge">
                        {getPaymentTypeLabel(invoice.payment_type)}
                      </span>
                    </div>
                    <span className="invoice-amount">
                      {invoice.amount_total.toLocaleString('cs-CZ')} {invoice.currency}
                    </span>
                  </div>

                  <div className="invoice-details">
                    <div className="detail-row">
                      <span className="label">{t('amountWithoutVat')}</span>
                      <span>{invoice.amount_without_vat.toLocaleString('cs-CZ')} Kc</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">{t('vatLabel', { rate: invoice.vat_rate })}</span>
                      <span>{(invoice.vat_amount || 0).toLocaleString('cs-CZ')} Kc</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">{t('issueDate')}</span>
                      <span>{new Date(invoice.issue_date).toLocaleDateString('cs-CZ')}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">{t('dueDateLabel')}</span>
                      <span>{new Date(invoice.due_date).toLocaleDateString('cs-CZ')}</span>
                    </div>
                    {invoice.paid_date && (
                      <div className="detail-row">
                        <span className="label">{t('paidDate')}</span>
                        <span>{new Date(invoice.paid_date).toLocaleDateString('cs-CZ')}</span>
                      </div>
                    )}
                    {invoice.variable_symbol && (
                      <div className="detail-row">
                        <span className="label">{t('varSymbol')}</span>
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
                    <button
                      className="btn-secondary"
                      onClick={() => handleGenerateAndDownloadPdf(invoice.id)}
                      disabled={generatingPdf === invoice.id}
                    >
                      {generatingPdf === invoice.id ? t('generatingPdf') : t('downloadPdf')}
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => router.push(`/${locale}/dashboard/invoices/${invoice.id}`)}
                    >
                      {tc('detail')}
                    </button>
                    {invoice.status === 'draft' && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'issued')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        {updatingInvoice === invoice.id ? t('updating') : t('issue')}
                      </button>
                    )}
                    {(invoice.status === 'issued' || invoice.status === 'overdue') && (
                      <button
                        className="btn-primary"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'paid')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        {updatingInvoice === invoice.id ? t('updating') : t('markAsPaid')}
                      </button>
                    )}
                    {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                      <button
                        className="btn-danger"
                        onClick={() => handleUpdateInvoiceStatus(invoice.id, 'cancelled')}
                        disabled={updatingInvoice === invoice.id}
                      >
                        {t('cancel')}
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
            <h3>{t('projectInfo')}</h3>
            <div className="settings-grid">
              <div className="setting-item">
                <label>{t('packageLabel')}</label>
                <span>{project.package}</span>
              </div>
              <div className="setting-item">
                <label>{t('statusLabel')}</label>
                <span>{getStatusLabel(project.status)}</span>
              </div>
              <div className="setting-item">
                <label>{t('domainLabel')}</label>
                <span>{project.domain || '-'}</span>
              </div>
              <div className="setting-item">
                <label>{t('domainStatusLabel')}</label>
                <span>
                  {getDomainStatusLabel(project.domain_status || 'planned')}
                </span>
              </div>
              <div className="setting-item">
                <label>{t('priceSetup')}</label>
                <span>
                  {project.price_setup
                    ? `${project.price_setup.toLocaleString('cs-CZ')} Kc`
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>{t('priceMonthly')}</label>
                <span>
                  {project.price_monthly
                    ? `${project.price_monthly.toLocaleString('cs-CZ')} Kc`
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>{t('deadline')}</label>
                <span>
                  {project.required_deadline
                    ? new Date(project.required_deadline).toLocaleDateString('cs-CZ')
                    : '-'}
                </span>
              </div>
              <div className="setting-item">
                <label>{t('budget')}</label>
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
              <h3>{t('notesTitle')}</h3>
              <p>{project.notes}</p>
            </div>
          )}

          {project.internal_notes && (
            <div className="settings-card">
              <h3>{t('internalNotes')}</h3>
              <p>{project.internal_notes}</p>
            </div>
          )}

          {project.client_notes && (
            <div className="settings-card">
              <h3>{t('clientNotes')}</h3>
              <p>{project.client_notes}</p>
            </div>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{t('deleteVersionConfirm')}</h3>
            <p>{t('deleteVersionWarning')}</p>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowDeleteModal(null)}
                disabled={deleting === showDeleteModal}
              >
                {tc('cancel')}
              </button>
              <button
                className="btn-danger"
                onClick={() => handleDeleteVersion(showDeleteModal)}
                disabled={deleting === showDeleteModal}
              >
                {deleting === showDeleteModal ? t('deletingVersion') : tc('delete')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Project Confirmation Modal */}
      {showDeleteProjectModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>{t('deleteProjectConfirm')}</h3>
            <p>
              <strong>{t('deleteProjectWarningTitle')}</strong> {t('deleteVersionWarning')}
            </p>
            <ul className="modal-warnings">
              <li>{t('deleteProjectWarning1')}</li>
              <li>{t('deleteProjectWarning2')}</li>
              <li>{t('deleteProjectWarning3')}</li>
            </ul>
            <p>
              {t('deleteProjectDeployWarning')}
            </p>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setShowDeleteProjectModal(false)}
                disabled={deletingProject}
              >
                {tc('cancel')}
              </button>
              <button
                className="btn-danger"
                onClick={handleDeleteProject}
                disabled={deletingProject}
              >
                {deletingProject ? t('deletingProject') : t('deleteProject')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Invoice Modal */}
      {showInvoiceModal && (
        <div className="modal-overlay">
          <div className="modal invoice-modal">
            <h3>{t('createInvoiceTitle')}</h3>
            <div className="invoice-form">
              <div className="form-group">
                <label>{t('amountWithoutVatLabel')}</label>
                <input
                  type="number"
                  value={invoiceForm.amount_without_vat}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, amount_without_vat: parseFloat(e.target.value) || 0 })}
                  placeholder="0"
                />
              </div>

              <div className="form-group">
                <label>{t('paymentType')}</label>
                <select
                  value={invoiceForm.payment_type}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, payment_type: e.target.value as 'setup' | 'monthly' | 'other' })}
                >
                  <option value="setup">{t('paymentSetup')}</option>
                  <option value="monthly">{t('paymentMonthly')}</option>
                  <option value="other">{t('paymentOther')}</option>
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>{t('vatRateLabel')}</label>
                  <input
                    type="number"
                    value={invoiceForm.vat_rate}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, vat_rate: parseFloat(e.target.value) || 21 })}
                  />
                </div>

                <div className="form-group">
                  <label>{t('dueDaysLabel')}</label>
                  <input
                    type="number"
                    value={invoiceForm.due_days}
                    onChange={(e) => setInvoiceForm({ ...invoiceForm, due_days: parseInt(e.target.value) || 14 })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>{t('descriptionOptional')}</label>
                <textarea
                  value={invoiceForm.description}
                  onChange={(e) => setInvoiceForm({ ...invoiceForm, description: e.target.value })}
                  placeholder={t('descriptionPlaceholder')}
                  rows={3}
                />
              </div>

              <div className="invoice-preview">
                <div className="preview-row">
                  <span>{t('amountWithoutVat')}</span>
                  <span>{invoiceForm.amount_without_vat.toLocaleString('cs-CZ')} Kc</span>
                </div>
                <div className="preview-row">
                  <span>{t('vatLabel', { rate: invoiceForm.vat_rate })}</span>
                  <span>{(invoiceForm.amount_without_vat * (invoiceForm.vat_rate / 100)).toLocaleString('cs-CZ')} Kc</span>
                </div>
                <div className="preview-row total">
                  <span>{t('totalLabel')}</span>
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
                {tc('cancel')}
              </button>
              <button
                className="btn-primary"
                onClick={handleCreateInvoice}
                disabled={creatingInvoice || invoiceForm.amount_without_vat <= 0}
              >
                {creatingInvoice ? t('creating') : t('createInvoiceButton')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
