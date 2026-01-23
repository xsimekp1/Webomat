'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import ApiClient from '../../../lib/api'

interface Business {
  id: string
  name: string
  address: string | null
  phone: string | null
  email: string | null
  website: string | null
  category: string | null
  notes: string | null
  status_crm: string
  owner_seller_id: string | null
  owner_seller_name: string | null
  next_follow_up_at: string | null
  created_at: string | null
  updated_at: string | null
  // Fakturační údaje
  ico: string | null
  dic: string | null
  billing_address: string | null
  bank_account: string | null
  contact_person: string | null
}

interface Activity {
  id: string
  business_id: string
  seller_id: string
  seller_name: string | null
  activity_type: string
  description: string
  outcome: string | null
  duration_minutes: number | null
  created_at: string | null
}

interface Project {
  id: string
  business_id: string
  package: string
  status: string
  price_setup: number | null
  price_monthly: number | null
  domain: string | null
  notes: string | null
  created_at: string | null
  updated_at: string | null
  latest_version_id: string | null
  versions_count: number
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  new: { label: 'Nový', color: '#3b82f6', bg: '#dbeafe' },
  calling: { label: 'Voláno', color: '#eab308', bg: '#fef9c3' },
  interested: { label: 'Zájem', color: '#f97316', bg: '#ffedd5' },
  offer_sent: { label: 'Nabídka', color: '#8b5cf6', bg: '#ede9fe' },
  won: { label: 'Vyhráno', color: '#22c55e', bg: '#dcfce7' },
  lost: { label: 'Ztraceno', color: '#6b7280', bg: '#f3f4f6' },
  dnc: { label: 'DNC', color: '#ef4444', bg: '#fee2e2' },
}

const ACTIVITY_ICONS: Record<string, string> = {
  call: '📞',
  email: '📧',
  meeting: '🤝',
  note: '📝',
  message: '💬',
}

const PROJECT_STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  offer: { label: 'Nabídka', color: '#8b5cf6', bg: '#ede9fe' },
  won: { label: 'Vyhráno', color: '#22c55e', bg: '#dcfce7' },
  in_production: { label: 'Ve výrobě', color: '#f97316', bg: '#ffedd5' },
  delivered: { label: 'Dodáno', color: '#3b82f6', bg: '#dbeafe' },
  live: { label: 'Live', color: '#10b981', bg: '#d1fae5' },
  cancelled: { label: 'Zrušeno', color: '#6b7280', bg: '#f3f4f6' },
}

const PACKAGE_CONFIG: Record<string, { label: string; color: string }> = {
  start: { label: 'Start', color: '#3b82f6' },
  profi: { label: 'Profi', color: '#8b5cf6' },
  premium: { label: 'Premium', color: '#f59e0b' },
  custom: { label: 'Custom', color: '#ec4899' },
}

export default function BusinessDetailPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const businessId = params.id as string

  const [business, setBusiness] = useState<Business | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Activity form
  const [showActivityModal, setShowActivityModal] = useState(false)
  const [activityForm, setActivityForm] = useState({
    activity_type: 'call',
    description: '',
    outcome: '',
    new_status: '',
  })
  const [saving, setSaving] = useState(false)

  // Status change
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [newStatus, setNewStatus] = useState('')

  // Delete
  const [deleting, setDeleting] = useState(false)

  // Project form
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [projectForm, setProjectForm] = useState({
    package: 'start',
    status: 'offer',
    price_setup: '',
    price_monthly: '',
    domain: '',
    notes: '',
  })

  // Website generation
  const [showWebsiteModal, setShowWebsiteModal] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [generatingWebsite, setGeneratingWebsite] = useState(false)
  const [generatedWebsite, setGeneratedWebsite] = useState<{html_content?: string; message?: string} | null>(null)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isLoading, isAuthenticated, router])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [businessRes, activitiesRes, projectsRes] = await Promise.all([
        ApiClient.getBusiness(businessId),
        ApiClient.getBusinessActivities(businessId),
        ApiClient.getBusinessProjects(businessId),
      ])
      setBusiness(businessRes)
      setActivities(activitiesRes)
      setProjects(projectsRes || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při načítání dat')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated && businessId) {
      fetchData()
    }
  }, [isAuthenticated, businessId])

  const handleAddActivity = async () => {
    if (!activityForm.description.trim()) {
      setError('Popis aktivity je povinný')
      return
    }

    setSaving(true)
    setError('')

    try {
      await ApiClient.createActivity(businessId, {
        activity_type: activityForm.activity_type,
        description: activityForm.description,
        outcome: activityForm.outcome || null,
        new_status: activityForm.new_status || null,
      })

      setShowActivityModal(false)
      setActivityForm({
        activity_type: 'call',
        description: '',
        outcome: '',
        new_status: '',
      })
      fetchData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při ukládání')
    } finally {
      setSaving(false)
    }
  }

  const handleStatusChange = async () => {
    if (!newStatus) return

    setSaving(true)
    setError('')

    try {
      await ApiClient.updateBusiness(businessId, { status_crm: newStatus })
      setShowStatusModal(false)
      fetchData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při změně statusu')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Opravdu chcete smazat tuto firmu? Tato akce je nevratná.')) {
      return
    }

    setDeleting(true)
    setError('')

    try {
      await ApiClient.deleteBusiness(businessId)
      router.push('/dashboard/crm')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při mazání')
      setDeleting(false)
    }
  }

  const openProjectModal = (projectToEdit?: Project) => {
    if (projectToEdit) {
      setEditingProject(projectToEdit)
      setProjectForm({
        package: projectToEdit.package,
        status: projectToEdit.status,
        price_setup: projectToEdit.price_setup?.toString() || '',
        price_monthly: projectToEdit.price_monthly?.toString() || '',
        domain: projectToEdit.domain || '',
        notes: projectToEdit.notes || '',
      })
    } else {
      setEditingProject(null)
      setProjectForm({
        package: 'start',
        status: 'offer',
        price_setup: '',
        price_monthly: '',
        domain: '',
        notes: '',
      })
    }
    setShowProjectModal(true)
  }

  const handleSaveProject = async () => {
    setSaving(true)
    setError('')

    const data = {
      package: projectForm.package,
      status: projectForm.status,
      price_setup: projectForm.price_setup ? parseFloat(projectForm.price_setup) : null,
      price_monthly: projectForm.price_monthly ? parseFloat(projectForm.price_monthly) : null,
      domain: projectForm.domain || null,
      notes: projectForm.notes || null,
    }

    try {
      if (editingProject) {
        await ApiClient.updateProject(editingProject.id, data)
      } else {
        await ApiClient.createProject(businessId, data)
      }
      setShowProjectModal(false)
      setEditingProject(null)
      fetchData()
    } catch (err: any) {
      console.error('Project save error:', err)
      const detail = err.response?.data?.detail || err.message || 'Neznámá chyba'
      const status = err.response?.status || 'N/A'
      setError(`[${status}] ${detail}`)
    } finally {
      setSaving(false)
    }
  }

  const handleGenerateWebsite = async (projectId: string, dryRun: boolean = false) => {
    setGeneratingWebsite(true)
    setError('')
    setGeneratedWebsite(null)

    try {
      const result = await ApiClient.generateWebsite(projectId, dryRun)
      setGeneratedWebsite(result)
      setShowWebsiteModal(false)
    } catch (err: any) {
      console.error('Website generation error:', err)
      const detail = err.response?.data?.detail || err.message || 'Chyba při generování webu'
      const status = err.response?.status || 'N/A'
      setError(`[${status}] ${detail}`)
    } finally {
      setGeneratingWebsite(false)
    }
  }

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('cs-CZ', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('cs-CZ')
  }

  if (isLoading || !user) {
    return <div className="loading">Načítám...</div>
  }

  if (loading) {
    return <div className="loading">Načítám detail...</div>
  }

  if (!business) {
    return (
      <div className="error-page">
        <h2>Lead nenalezen</h2>
        <button onClick={() => router.push('/dashboard/crm')}>Zpět na seznam</button>
      </div>
    )
  }

  return (
    <div className="detail-page">
      <header className="detail-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.push('/dashboard/crm')}>
            ← Zpět
          </button>
          <div className="business-title">
            <h1>{business.name}</h1>
            <span
              className="status-badge"
              style={{
                color: STATUS_CONFIG[business.status_crm]?.color || '#666',
                backgroundColor: STATUS_CONFIG[business.status_crm]?.bg || '#f5f5f5',
              }}
              onClick={() => { setNewStatus(business.status_crm); setShowStatusModal(true); }}
            >
              {STATUS_CONFIG[business.status_crm]?.label || business.status_crm} ▾
            </span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-activity" onClick={() => setShowActivityModal(true)}>
            + Přidat aktivitu
          </button>
          <button className="btn-delete" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Mažu...' : 'Smazat'}
          </button>
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      <div className="detail-grid">
        {/* Info Card */}
        <div className="card info-card">
          <h3>Kontaktní údaje</h3>

          <div className="info-row">
            <span className="label">Telefon:</span>
            {business.phone ? (
              <a href={`tel:${business.phone}`} className="phone-link">{business.phone}</a>
            ) : (
              <span className="empty">-</span>
            )}
          </div>

          <div className="info-row">
            <span className="label">Email:</span>
            {business.email ? (
              <a href={`mailto:${business.email}`} className="email-link">{business.email}</a>
            ) : (
              <span className="empty">-</span>
            )}
          </div>

          <div className="info-row">
            <span className="label">Adresa:</span>
            <span>{business.address || '-'}</span>
          </div>

          <div className="info-row">
            <span className="label">Web:</span>
            {business.website ? (
              <a href={business.website} target="_blank" rel="noopener noreferrer" className="web-link">
                {business.website}
              </a>
            ) : (
              <span className="empty">-</span>
            )}
          </div>

          <div className="info-row">
            <span className="label">Kategorie:</span>
            <span>{business.category || '-'}</span>
          </div>

          <div className="info-row">
            <span className="label">Follow-up:</span>
            <span className={business.next_follow_up_at && new Date(business.next_follow_up_at) < new Date() ? 'overdue' : ''}>
              {formatDate(business.next_follow_up_at)}
            </span>
          </div>

          <div className="info-row">
            <span className="label">Přiřazeno:</span>
            <span>{business.owner_seller_name || 'Nepřiřazeno'}</span>
          </div>

          {/* Fakturační údaje */}
          {(business.ico || business.dic || business.billing_address || business.bank_account || business.contact_person) && (
            <div className="billing-section">
              <h4>Fakturační údaje</h4>

              {business.ico && (
                <div className="info-row">
                  <span className="label">IČO:</span>
                  <span>{business.ico}</span>
                </div>
              )}

              {business.dic && (
                <div className="info-row">
                  <span className="label">DIČ:</span>
                  <span>{business.dic}</span>
                </div>
              )}

              {business.contact_person && (
                <div className="info-row">
                  <span className="label">Kontakt:</span>
                  <span>{business.contact_person}</span>
                </div>
              )}

              {business.billing_address && (
                <div className="info-row">
                  <span className="label">Fakt. adresa:</span>
                  <span>{business.billing_address}</span>
                </div>
              )}

              {business.bank_account && (
                <div className="info-row">
                  <span className="label">Účet:</span>
                  <span className="bank-account">{business.bank_account}</span>
                </div>
              )}
            </div>
          )}

          {business.notes && (
            <div className="notes-section">
              <h4>Poznámky</h4>
              <p>{business.notes}</p>
            </div>
          )}

          <div className="meta-info">
            <span>Vytvořeno: {formatDateTime(business.created_at)}</span>
            {business.updated_at && (
              <span>Upraveno: {formatDateTime(business.updated_at)}</span>
            )}
          </div>
        </div>

        {/* Projects Card */}
        <div className="card project-card">
          <div className="card-header-row">
            <h3>Projekty ({projects.length})</h3>
            <button className="btn-edit-small" onClick={() => openProjectModal()}>
              + Nový projekt
            </button>
          </div>

          {projects.length > 0 ? (
            <div className="projects-list">
              {projects.map((project) => (
                <div key={project.id} className="project-content" onClick={() => openProjectModal(project)} style={{ cursor: 'pointer' }}>
                  <div className="project-header">
                    <span
                      className="package-badge"
                      style={{ color: PACKAGE_CONFIG[project.package]?.color || '#666' }}
                    >
                      {PACKAGE_CONFIG[project.package]?.label || project.package}
                    </span>
                    <span
                      className="project-status-badge"
                      style={{
                        color: PROJECT_STATUS_CONFIG[project.status]?.color || '#666',
                        backgroundColor: PROJECT_STATUS_CONFIG[project.status]?.bg || '#f5f5f5',
                      }}
                    >
                      {PROJECT_STATUS_CONFIG[project.status]?.label || project.status}
                    </span>
                    {project.versions_count > 0 && (
                      <span className="versions-badge">
                        {project.versions_count} verzí
                      </span>
                    )}
                  </div>

                  <div className="project-prices">
                    {project.price_setup !== null && (
                      <div className="price-item">
                        <span className="price-label">Jednorázově:</span>
                        <span className="price-value">{project.price_setup.toLocaleString('cs-CZ')} Kč</span>
                      </div>
                    )}
                    {project.price_monthly !== null && (
                      <div className="price-item">
                        <span className="price-label">Měsíčně:</span>
                        <span className="price-value">{project.price_monthly.toLocaleString('cs-CZ')} Kč</span>
                      </div>
                    )}
                  </div>

                  {project.domain && (
                    <div className="info-row">
                      <span className="label">Doména:</span>
                      <a href={`https://${project.domain}`} target="_blank" rel="noopener noreferrer" className="web-link" onClick={(e) => e.stopPropagation()}>
                        {project.domain}
                      </a>
                    </div>
                  )}

                  {project.notes && (
                    <div className="project-notes">
                      <p>{project.notes}</p>
                    </div>
                  )}

                  {/* Website Preview */}
                  {project.latest_version_id && (
                    <div className="project-preview" onClick={(e) => e.stopPropagation()}>
                      <div className="preview-header">
                        <span className="preview-label">📸 Náhled webu</span>
                        <span className="preview-version">v{project.versions_count}</span>
                      </div>
                      <div className="preview-placeholder">
                        <span>Náhled bude zde</span>
                      </div>
                    </div>
                  )}

                  <div className="project-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="btn-generate-web"
                      onClick={() => {
                        setSelectedProjectId(project.id)
                        setShowWebsiteModal(true)
                      }}
                      disabled={generatingWebsite}
                    >
                      {generatingWebsite ? 'Generuji...' : '🚀 Generovat web'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-project">
              <p>Zatím žádný projekt</p>
              <span className="hint">Vytvořte projekt po uzavření dealu</span>
            </div>
          )}
        </div>

        {/* Activities Card */}
        <div className="card activities-card">
          <h3>Komunikační log ({activities.length})</h3>

          {activities.length === 0 ? (
            <div className="empty-activities">
              <p>Zatím žádné aktivity</p>
            </div>
          ) : (
            <div className="activities-list">
              {activities.map((activity) => (
                <div key={activity.id} className="activity-item">
                  <div className="activity-icon">
                    {ACTIVITY_ICONS[activity.activity_type] || '📋'}
                  </div>
                  <div className="activity-content">
                    <div className="activity-header">
                      <span className="activity-type">{activity.activity_type}</span>
                      <span className="activity-date">{formatDateTime(activity.created_at)}</span>
                    </div>
                    <p className="activity-description">{activity.description}</p>
                    {activity.outcome && (
                      <p className="activity-outcome">Výsledek: {activity.outcome}</p>
                    )}
                    <span className="activity-seller">— {activity.seller_name || 'Neznámý'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Activity Modal */}
      {showActivityModal && (
        <div className="modal-overlay" onClick={() => setShowActivityModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Přidat aktivitu</h2>

            <div className="form-group">
              <label>Typ aktivity</label>
              <select
                value={activityForm.activity_type}
                onChange={(e) => setActivityForm({ ...activityForm, activity_type: e.target.value })}
              >
                <option value="call">📞 Hovor</option>
                <option value="email">📧 Email</option>
                <option value="meeting">🤝 Schůzka</option>
                <option value="note">📝 Poznámka</option>
                <option value="message">💬 Zpráva</option>
              </select>
            </div>

            <div className="form-group">
              <label>Popis *</label>
              <textarea
                value={activityForm.description}
                onChange={(e) => setActivityForm({ ...activityForm, description: e.target.value })}
                placeholder="Co se stalo..."
                rows={4}
              />
            </div>

            <div className="form-group">
              <label>Výsledek</label>
              <input
                type="text"
                value={activityForm.outcome}
                onChange={(e) => setActivityForm({ ...activityForm, outcome: e.target.value })}
                placeholder="Volat zítra, poslat nabídku..."
              />
            </div>

            <div className="form-group">
              <label>Změnit status na</label>
              <select
                value={activityForm.new_status}
                onChange={(e) => setActivityForm({ ...activityForm, new_status: e.target.value })}
              >
                <option value="">Bez změny</option>
                {Object.entries(STATUS_CONFIG).map(([key, { label }]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowActivityModal(false)}>
                Zrušit
              </button>
              <button className="btn-primary" onClick={handleAddActivity} disabled={saving}>
                {saving ? 'Ukládám...' : 'Přidat'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Project Modal */}
      {showProjectModal && (
        <div className="modal-overlay" onClick={() => setShowProjectModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingProject ? 'Upravit projekt' : 'Vytvořit projekt'}</h2>

            <div className="form-row">
              <div className="form-group">
                <label>Balíček</label>
                <select
                  value={projectForm.package}
                  onChange={(e) => setProjectForm({ ...projectForm, package: e.target.value })}
                >
                  <option value="start">Start</option>
                  <option value="profi">Profi</option>
                  <option value="premium">Premium</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div className="form-group">
                <label>Status</label>
                <select
                  value={projectForm.status}
                  onChange={(e) => setProjectForm({ ...projectForm, status: e.target.value })}
                >
                  {Object.entries(PROJECT_STATUS_CONFIG).map(([key, { label }]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Cena jednorázově (Kč)</label>
                <input
                  type="number"
                  value={projectForm.price_setup}
                  onChange={(e) => setProjectForm({ ...projectForm, price_setup: e.target.value })}
                  placeholder="0"
                />
              </div>

              <div className="form-group">
                <label>Cena měsíčně (Kč)</label>
                <input
                  type="number"
                  value={projectForm.price_monthly}
                  onChange={(e) => setProjectForm({ ...projectForm, price_monthly: e.target.value })}
                  placeholder="0"
                />
              </div>
            </div>

            <div className="form-group">
              <label>Doména</label>
              <input
                type="text"
                value={projectForm.domain}
                onChange={(e) => setProjectForm({ ...projectForm, domain: e.target.value })}
                placeholder="example.cz"
              />
            </div>

            <div className="form-group">
              <label>Poznámky k projektu</label>
              <textarea
                value={projectForm.notes}
                onChange={(e) => setProjectForm({ ...projectForm, notes: e.target.value })}
                placeholder="Detaily projektu..."
                rows={3}
              />
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowProjectModal(false)}>
                Zrušit
              </button>
              <button className="btn-primary" onClick={handleSaveProject} disabled={saving}>
                {saving ? 'Ukládám...' : 'Uložit'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Change Modal */}
      {showStatusModal && (
        <div className="modal-overlay" onClick={() => setShowStatusModal(false)}>
          <div className="modal modal-small" onClick={(e) => e.stopPropagation()}>
            <h2>Změnit status</h2>

            <div className="status-options">
              {Object.entries(STATUS_CONFIG).map(([key, { label, color, bg }]) => (
                <button
                  key={key}
                  className={`status-option ${newStatus === key ? 'selected' : ''}`}
                  style={{ borderColor: color, backgroundColor: newStatus === key ? bg : 'white' }}
                  onClick={() => setNewStatus(key)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowStatusModal(false)}>
                Zrušit
              </button>
              <button className="btn-primary" onClick={handleStatusChange} disabled={saving}>
                {saving ? 'Ukládám...' : 'Uložit'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Website Generation Modal */}
      {showWebsiteModal && (
        <div className="modal-overlay" onClick={() => setShowWebsiteModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Generování webové stránky</h2>

            <div className="website-gen-options">
              <div className="option-card" onClick={() => handleGenerateWebsite(selectedProjectId, true)}>
                <h3>🔧 DRY RUN Test</h3>
                <p>Vygeneruje testovací stránku bez volání AI API. Ideální pro testování funkcionality.</p>
                <button className="btn-primary" disabled={generatingWebsite}>
                  {generatingWebsite ? 'Generuji...' : 'Spustit DRY RUN'}
                </button>
              </div>

              <div className="option-card disabled">
                <h3>🤖 AI Generování</h3>
                <p>Plné generování pomocí Claude API (zatím není implementováno)</p>
                <button className="btn-secondary" disabled>
                  Brzy dostupné
                </button>
              </div>
            </div>

            {generatedWebsite && (
              <div className="generation-result">
                <h3>Výsledek generování:</h3>
                <p>{generatedWebsite.message}</p>
                {generatedWebsite.html_content && (
                  <div className="html-preview">
                    <iframe
                      srcDoc={generatedWebsite.html_content}
                      width="100%"
                      height="300"
                      style={{ border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                )}
              </div>
            )}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowWebsiteModal(false)}>
                Zrušit
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .detail-page {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 24px;
        }

        .header-left {
          display: flex;
          align-items: flex-start;
          gap: 16px;
        }

        .business-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .business-title h1 {
          margin: 0;
          font-size: 28px;
          color: #1a1a2e;
        }

        .btn-back {
          background: none;
          border: 1px solid #ddd;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          color: #666;
          margin-top: 4px;
        }

        .btn-back:hover {
          background: #f5f5f5;
        }

        .status-badge {
          display: inline-block;
          padding: 6px 14px;
          border-radius: 16px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
        }

        .status-badge:hover {
          opacity: 0.8;
        }

        .header-actions {
          display: flex;
          gap: 12px;
        }

        .btn-activity {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-delete {
          background: #fee2e2;
          color: #dc2626;
          border: 1px solid #fecaca;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-delete:hover {
          background: #fecaca;
        }

        .btn-delete:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-message {
          background: #fee2e2;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 6px;
          margin-bottom: 16px;
        }

        .detail-grid {
          display: grid;
          grid-template-columns: 350px 1fr;
          gap: 24px;
          align-items: start;
        }

        .detail-grid > .info-card,
        .detail-grid > .project-card {
          grid-column: 1;
        }

        .detail-grid > .activities-card {
          grid-column: 2;
          grid-row: 1 / span 2;
        }

        .card {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .card h3 {
          margin: 0 0 20px;
          color: #1a1a2e;
          font-size: 18px;
        }

        .info-row {
          display: flex;
          padding: 10px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .info-row .label {
          width: 100px;
          color: #666;
          font-size: 14px;
        }

        .info-row .empty {
          color: #999;
        }

        .phone-link,
        .email-link,
        .web-link {
          color: #667eea;
          text-decoration: none;
        }

        .phone-link:hover,
        .email-link:hover,
        .web-link:hover {
          text-decoration: underline;
        }

        .overdue {
          color: #dc2626;
          font-weight: 600;
        }

        .billing-section {
          margin-top: 20px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
        }

        .billing-section h4 {
          margin: 0 0 12px;
          font-size: 14px;
          color: #666;
          font-weight: 600;
        }

        .bank-account {
          font-family: monospace;
          background: #f3f4f6;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .card-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .card-header-row h3 {
          margin: 0;
        }

        .btn-edit-small {
          padding: 6px 12px;
          font-size: 13px;
          background: #f5f5f5;
          border: 1px solid #ddd;
          border-radius: 6px;
          cursor: pointer;
          color: #666;
        }

        .btn-edit-small:hover {
          background: #e5e5e5;
        }

        .project-content {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .project-header {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .package-badge {
          font-size: 18px;
          font-weight: 700;
        }

        .project-status-badge {
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .versions-badge {
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          background-color: #e0f2fe;
          color: #0369a1;
          margin-left: 8px;
        }

        .project-prices {
          display: flex;
          gap: 20px;
          padding: 12px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .price-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .price-label {
          font-size: 12px;
          color: #666;
        }

        .price-value {
          font-size: 16px;
          font-weight: 600;
          color: #1a1a2e;
        }

        .project-notes {
          font-size: 14px;
          color: #374151;
          line-height: 1.5;
          padding-top: 8px;
          border-top: 1px solid #f0f0f0;
        }

        .project-notes p {
          margin: 0;
        }

        .empty-project {
          text-align: center;
          padding: 24px 16px;
          color: #666;
        }

        .empty-project p {
          margin: 0 0 4px;
        }

        .empty-project .hint {
          font-size: 12px;
          color: #999;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .notes-section {
          margin-top: 20px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
        }

        .notes-section h4 {
          margin: 0 0 8px;
          font-size: 14px;
          color: #666;
        }

        .notes-section p {
          margin: 0;
          color: #374151;
          line-height: 1.6;
        }

        .meta-info {
          margin-top: 20px;
          padding-top: 16px;
          border-top: 1px solid #e5e7eb;
          font-size: 12px;
          color: #999;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .empty-activities {
          text-align: center;
          padding: 40px 20px;
          color: #666;
        }

        .btn-activity-small {
          margin-top: 12px;
          padding: 8px 16px;
          background: #f5f5f5;
          border: 1px solid #ddd;
          border-radius: 6px;
          cursor: pointer;
        }

        .activities-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .activity-item {
          display: flex;
          gap: 12px;
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .activity-icon {
          font-size: 24px;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border-radius: 8px;
        }

        .activity-content {
          flex: 1;
        }

        .activity-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .activity-type {
          font-weight: 600;
          text-transform: capitalize;
          color: #374151;
        }

        .activity-date {
          font-size: 12px;
          color: #999;
        }

        .activity-description {
          margin: 0 0 8px;
          color: #1a1a2e;
          line-height: 1.5;
        }

        .activity-outcome {
          margin: 0 0 8px;
          font-size: 13px;
          color: #666;
          font-style: italic;
        }

        .activity-seller {
          font-size: 12px;
          color: #999;
        }

        .project-preview {
          margin-top: 12px;
          padding: 12px;
          background: #f8fafc;
          border-radius: 8px;
          border: 1px solid #e5e7eb;
        }

        .preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .preview-label {
          font-size: 12px;
          font-weight: 600;
          color: #374151;
        }

        .preview-version {
          font-size: 10px;
          color: #6b7280;
          background: #e5e7eb;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .preview-placeholder {
          height: 60px;
          background: #fff;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .preview-placeholder span {
          font-size: 12px;
          color: #9ca3af;
        }

        .project-actions {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid #f0f0f0;
        }

        .btn-generate-web {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          transition: opacity 0.2s;
        }

        .btn-generate-web:hover:not(:disabled) {
          opacity: 0.9;
        }

        .btn-generate-web:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .website-gen-options {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          margin-bottom: 24px;
        }

        .option-card {
          padding: 20px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: border-color 0.2s;
        }

        .option-card:hover:not(.disabled) {
          border-color: #667eea;
        }

        .option-card.disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .option-card h3 {
          margin: 0 0 8px;
          font-size: 16px;
          color: #1a1a2e;
        }

        .option-card p {
          margin: 0 0 16px;
          font-size: 14px;
          color: #666;
          line-height: 1.4;
        }

        .generation-result {
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
        }

        .generation-result h3 {
          margin: 0 0 12px;
          color: #1a1a2e;
          font-size: 16px;
        }

        .generation-result p {
          margin: 0 0 16px;
          color: #374151;
        }

        .html-preview {
          margin-top: 16px;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: white;
          border-radius: 12px;
          padding: 24px;
          width: 90%;
          max-width: 500px;
        }

        .modal-small {
          max-width: 400px;
        }

        .modal h2 {
          margin: 0 0 20px;
          color: #1a1a2e;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-group label {
          display: block;
          margin-bottom: 6px;
          font-weight: 500;
          color: #374151;
          font-size: 14px;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .form-group textarea {
          resize: vertical;
        }

        .status-options {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          margin-bottom: 20px;
        }

        .status-option {
          padding: 12px;
          border: 2px solid #ddd;
          background: white;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
        }

        .status-option.selected {
          border-width: 2px;
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 24px;
        }

        .btn-secondary {
          padding: 10px 20px;
          background: #f5f5f5;
          border: 1px solid #ddd;
          border-radius: 6px;
          cursor: pointer;
        }

        .btn-primary {
          padding: 10px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .loading,
        .error-page {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          gap: 16px;
          color: #666;
        }

        .error-page button {
          padding: 10px 20px;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }

        @media (max-width: 900px) {
          .detail-grid {
            grid-template-columns: 1fr;
          }

          .detail-grid > .info-card,
          .detail-grid > .project-card,
          .detail-grid > .activities-card {
            grid-column: 1;
            grid-row: auto;
          }

          .detail-header {
            flex-direction: column;
            gap: 16px;
          }

          .business-title {
            flex-direction: column;
            align-items: flex-start;
          }

          .form-row {
            grid-template-columns: 1fr;
          }

          .project-prices {
            flex-direction: column;
            gap: 12px;
          }
        }
      `}</style>
    </div>
  )
}
