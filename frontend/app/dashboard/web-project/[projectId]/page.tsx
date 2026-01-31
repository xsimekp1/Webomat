'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { useToast } from '../../../context/ToastContext'
import ApiClient from '../../../lib/api'
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
  expires_at: string | null
  view_count: number
  is_active: boolean
}

const STATUS_LABELS: Record<string, string> = {
  offer: 'Nabidka',
  won: 'Vyhrano',
  in_production: 'Ve vyrobe',
  delivered: 'Dodano',
  live: 'Online',
  cancelled: 'Zruseno',
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

export default function WebProjectPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const projectId = params.projectId as string

  const [project, setProject] = useState<Project | null>(null)
  const [versions, setVersions] = useState<Version[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'versions' | 'settings'>('versions')

  // Action states
  const [deploying, setDeploying] = useState<string | null>(null)
  const [capturing, setCapturing] = useState<string | null>(null)
  const [creatingLink, setCreatingLink] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [deletingProject, setDeletingProject] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null)
  const [showDeleteProjectModal, setShowDeleteProjectModal] = useState(false)
  const [shareLinks, setShareLinks] = useState<Record<string, ShareLink>>({})

  const loadProject = useCallback(async () => {
    try {
      setLoading(true)
      const [projectData, versionsData] = await Promise.all([
        ApiClient.getWebProject(projectId),
        ApiClient.getWebProjectVersions(projectId),
      ])
      setProject(projectData)
      setVersions(versionsData.items || [])
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

  // Testovací toasts - zobrazí se při načtení projektu
  useEffect(() => {
    if (project && project.id) {
      // Zobrazí testovací toast s názvem projektu
      setTimeout(() => showToast(`Projekt načten: ${project.id}`, 'info', 3000), 500)
      
      // Test dalších typů toastů
      setTimeout(() => showToast('Success toast - vše funguje!', 'success', 2000), 1000)
      setTimeout(() => showToast('Warning - pozor na tento projekt', 'warning', 2500), 1500)
      setTimeout(() => showToast('Error - něco se pokazilo (test)', 'error', 2000), 2000)
    }
  }, [project, showToast])

  const handleDeploy = async (versionId: string) => {
    setDeploying(versionId)
    try {
      await ApiClient.deployVersion(versionId)
      await loadProject()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se nasadit verzi')
    } finally {
      setDeploying(null)
    }
  }

  const handleUndeploy = async (versionId: string) => {
    if (!confirm('Opravdu chcete odebrat nasazeni?')) return
    try {
      await ApiClient.undeployVersion(versionId)
      await loadProject()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se odebrat nasazeni')
    }
  }

  const handleCaptureScreenshot = async (versionId: string) => {
    setCapturing(versionId)
    try {
      await ApiClient.captureScreenshot(versionId)
      alert('Screenshot byl zarazen do fronty')
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se vytvorit screenshot')
    } finally {
      setCapturing(null)
    }
  }

  const handleCreateShareLink = async (versionId: string) => {
    setCreatingLink(versionId)
    try {
      const link = await ApiClient.createShareLink(versionId, { expires_in_days: 7 })
      setShareLinks(prev => ({ ...prev, [versionId]: link }))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se vytvorit odkaz')
    } finally {
      setCreatingLink(null)
    }
  }

  const handleMarkAsCurrent = async (versionId: string) => {
    try {
      await ApiClient.markVersionAsCurrent(versionId)
      await loadProject()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se nastavit jako aktualni')
    }
  }

  const handleDeleteVersion = async (versionId: string) => {
    setDeleting(versionId)
    try {
      await ApiClient.deleteVersion(versionId)
      await loadProject()
      setShowDeleteModal(null)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se smazat verzi')
    } finally {
      setDeleting(null)
    }
  }

  const handleDeleteProject = async () => {
    setDeletingProject(true)
    try {
      await ApiClient.deleteProject(projectId)
      setShowDeleteProjectModal(false)
      // Redirect back to dashboard or projects list
      router.push('/dashboard')
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Nepodarilo se smazat projekt')
    } finally {
      setDeletingProject(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    alert('Odkaz byl zkopirovan')
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
        <button onClick={() => router.back()}>Zpet</button>
      </div>
    )
  }

  return (
    <div className="web-project-page">
      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.back()}>
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

                    {/* Screenshot */}
                    <button
                      className="btn-secondary"
                      onClick={() => handleCaptureScreenshot(version.id)}
                      disabled={capturing === version.id}
                    >
                      {capturing === version.id ? 'Zachycuje...' : 'Screenshot'}
                    </button>

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
    </div>
  )
}
