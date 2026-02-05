'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import ApiClient from '../../../../lib/api'
import { useAuth } from '../../../../context/AuthContext'
import { storeCrmPage } from '../../../../lib/navigation'

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
  // Kontaktní osoba (jedno pole)
  contact_name: string | null
  // Logo firmy
  logo_url: string | null
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
  latest_thumbnail_url: string | null
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  new: { label: 'Nový', color: '#3b82f6', bg: '#dbeafe' },
  calling: { label: 'Voláno', color: '#eab308', bg: '#fef9c3' },
  interested: { label: 'Zájem', color: '#f97316', bg: '#ffedd5' },
  offer_sent: { label: 'Nabídka', color: '#8b5cf6', bg: '#ede9fe' },
  designed: { label: 'Designováno', color: '#06b6d4', bg: '#cffafe' },
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
  interested: { label: 'Zájem', color: '#06b6d4', bg: '#ecfeff' },
  in_progress: { label: 'V práci', color: '#f97316', bg: '#ffedd5' },
  sent_for_review: { label: 'K odeslání', color: '#3b82f6', bg: '#dbeafe' },
  revisions: { label: 'Připomínky', color: '#a855f7', bg: '#f3e8ff' },
  invoiced: { label: 'Fakturováno', color: '#22c55e', bg: '#dcfce7' },
  closed: { label: 'Uzavřeno', color: '#6b7280', bg: '#f3f4f6' },
  rejected: { label: 'Zamítnuto', color: '#dc2626', bg: '#fef2f2' },
  unpaid: { label: 'Nezaplaceno', color: '#dc2626', bg: '#fef2f2' },
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
  const businessId = Array.isArray(params.id) ? params.id[0] : params.id
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
    next_follow_up_at: '',
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
      // Filter out cancelled projects for sales users
      const filteredProjects = (projectsRes || []).filter(project => 
        user?.role === 'admin' || project.status !== 'cancelled'
      )
      setProjects(filteredProjects)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při načítání dat')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated && businessId) {
      fetchData()
      // Store current CRM page for navigation back from project detail
      storeCrmPage(businessId)
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
        next_follow_up_at: activityForm.next_follow_up_at || null,
      })

      setShowActivityModal(false)
setActivityForm({
        activity_type: 'call',
        description: '',
        outcome: '',
        new_status: '',
        next_follow_up_at: '',
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

  const canCreateProject = (): boolean => {
    if (!user || !business) return false
    
    // Admin může vytvářet projekty pro jakoukoli firmu
    if (user.role === 'admin') return true
    
    // Sales může vytvářet jen pro vlastní firmy
    return business.owner_seller_id === user.id
  }

  const handleDeleteBusiness = async () => {
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

    // Validate form data before sending
    if (!projectForm.package) {
      setError('Balíček je povinný')
      setSaving(false)
      return
    }
    
    if (!projectForm.status) {
      setError('Status je povinný')
      setSaving(false)
      return
    }

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
      
      // Close modal immediately after successful save
      setShowProjectModal(false)
      setEditingProject(null)
      
      // Refresh data but don't let business become null if refresh fails
      try {
        fetchData()
      } catch (refreshErr) {
        console.error('Refresh failed after project save:', refreshErr)
        // Don't show error - project was saved successfully
      }
    } catch (err: any) {
      console.error('Project save error:', err)
      const detail = err.response?.data?.detail || err.message || 'Neznámá chyba'
      const status = err.response?.status || 'N/A'
      
      // Add more specific error handling
      if (status === 400) {
        if (detail.includes('package') || detail.includes('status')) {
          setError('Chyba v datech formuláře. Zkontrolujte balíček a status projektu.')
        } else if (detail.includes('access')) {
          setError('Nemáte oprávnění vytvořit projekt pro tuto firmu.')
        } else {
          setError(`Chyba dat: ${detail}`)
        }
      } else if (status === 403) {
        setError('Nemáte oprávnění vytvořit projekt pro tuto firmu.')
      } else if (status === 500) {
        setError('Chyba serveru. Zkuste to znovu později.')
      } else {
        setError(`[${status}] ${detail}`)
      }
    } finally {
      setSaving(false)
    }
  }

// Check if this is a test contact
const isTestContact = business?.name?.toLowerCase().includes('test') ||
                       business?.name?.toLowerCase().includes('demo') ||
                       business?.name?.toLowerCase().includes('sample')

const handleGenerateWebsite = async (projectId: string, dryRun: boolean = false) => {
  const businessName = business?.name || 'Neznámá firma'

  router.push(
    `/dashboard/generate-website?businessId=${encodeURIComponent(businessId)}&projectId=${encodeURIComponent(projectId)}&businessName=${encodeURIComponent(businessName)}&dryRun=${dryRun ? '1' : '0'}`
  )
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
    );
  }

  return (
    <div className="detail-page">
      <header className="detail-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.push('/dashboard/crm')}>
            ← Zpět
          </button>
          <div className="business-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h1>{business.name}</h1>
              {isTestContact && (
                <span className="test-badge" title="Testovací kontakt">
                  🧪 TEST
                </span>
              )}
            </div>
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

          {/* Kontaktní osoba */}
          {(business.contact_person || business.contact_name) && (
            <div className="info-row">
              <span className="label">Kontaktní osoba:</span>
              <span>{business.contact_name || business.contact_person || '-'}</span>
            </div>
          )}

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

        {/* Projects Card (Right Column) */}
        <div className="card projects-card">
          <div className="card-header-row">
            <h3>Projekty ({projects.length})</h3>
            {canCreateProject() && (
              <button className="btn-edit-small" onClick={() => openProjectModal()}>
                + Nový
              </button>
            )}
          </div>
          {projects.length > 0 ? (
            <div className="projects-list-mini">
              {projects.map((project) => (
                <div
                  key={project.id}
                  className="project-mini-card"
                  onClick={() => router.push(`/dashboard/web-project/${project.id}`)}
                >
                  <div className="project-mini-thumbnail">
                    {project.latest_thumbnail_url ? (
                      <img src={project.latest_thumbnail_url} alt="Náhled" />
                    ) : (
                      <div className="thumbnail-placeholder-mini">
                        <span>Bez náhledu</span>
                      </div>
                    )}
                  </div>
                  <div className="project-mini-info">
                    <div className="project-mini-header">
                      <span
                        className="project-status-badge-mini"
                        style={{
                          color: PROJECT_STATUS_CONFIG[project.status]?.color || '#666',
                          backgroundColor: PROJECT_STATUS_CONFIG[project.status]?.bg || '#f5f5f5',
                        }}
                      >
                        {PROJECT_STATUS_CONFIG[project.status]?.label || project.status}
                      </span>
                      <span
                        className="package-badge-mini"
                        style={{ color: PACKAGE_CONFIG[project.package]?.color || '#666' }}
                      >
                        {PACKAGE_CONFIG[project.package]?.label || project.package}
                      </span>
                    </div>
                    <span className="project-domain-mini">{project.domain || 'Bez domény'}</span>
                    {project.versions_count > 0 && (
                      <span className="versions-count-mini">{project.versions_count} verzí</span>
                    )}
                  </div>
                  <button
                    className="btn-manage-mini"
                    onClick={(e) => {
                      e.stopPropagation()
                      router.push(`/dashboard/web-project/${project.id}`)
                    }}
                    title="Správa webu"
                  >
                    🌐
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-projects">
              <p>Žádné projekty</p>
              <span className="hint">Klikněte + pro vytvoření</span>
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
              <label>Další follow-up</label>
              <input
                type="datetime-local"
                value={activityForm.next_follow_up_at}
                onChange={(e) => {
                  const selectedDate = new Date(e.target.value);
                  const now = new Date();
                  if (selectedDate >= now) {
                    setActivityForm({ ...activityForm, next_follow_up_at: e.target.value });
                  }
                }}
                min={new Date().toISOString().slice(0, 16)}
              />
              <small style={{ color: '#94a3b8', fontSize: '12px' }}>
                Nelze nastavit datum v minulosti
              </small>
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

      {/* Project Modal - TEMPORARILY DISABLED */}
      {/* {showProjectModal && (
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
      )} */}

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
            <h2>🌐 Generování webové stránky</h2>
            
            <div style={{ textAlign: 'center', padding: '30px 20px' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚀</div>
              <p style={{ fontSize: '16px', color: '#374151', marginBottom: '20px', lineHeight: '1.6' }}>
                Otevřu specializovanou stránku pro generování webu s velkým preview a možnostmi exportu.
              </p>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '30px' }}>
                Můžete vybrat mezi DRY RUN testem a plným AI generováním.
              </p>
              
              <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', flexWrap: 'wrap' }}>
                <button 
                  onClick={() => {
                    setShowWebsiteModal(false)
                    handleGenerateWebsite(selectedProjectId, true)
                  }}
                  disabled={generatingWebsite}
                  style={{
                    padding: '12px 24px',
                    background: '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: generatingWebsite ? 'not-allowed' : 'pointer'
                  }}
                >
                  🔧 DRY RUN Test
                </button>
                
                <button 
                  onClick={() => {
                    setShowWebsiteModal(false)
                    handleGenerateWebsite(selectedProjectId, false)
                  }}
                  disabled={generatingWebsite}
                  style={{
                    padding: '12px 24px',
                    background: '#f3f4f6',
                    color: '#6b7280',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'not-allowed'
                  }}
                >
                  🤖 AI Generování (brzy)
                </button>
              </div>
              
              {generatingWebsite && (
                <p style={{ marginTop: '20px', color: '#667eea', fontSize: '14px' }}>
                  ⏳ Přesměrování na generovací stránku...
                </p>
              )}
            </div>

            <div className="modal-actions" style={{ justifyContent: 'center' }}>
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
          max-width: 1400px;
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
          grid-template-columns: 350px 1fr 300px;
          gap: 24px;
          align-items: start;
        }

        .detail-grid > .info-card {
          grid-column: 1;
        }

        .detail-grid > .activities-card {
          grid-column: 2;
          grid-row: 1;
        }

        .detail-grid > .projects-card {
          grid-column: 3;
          grid-row: 1;
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

        /* Projects Card Styles (Right Column) */
        .projects-list-mini {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .project-mini-card {
          display: flex;
          gap: 12px;
          padding: 10px;
          background: #f9fafb;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          border: 1px solid transparent;
          position: relative;
        }

        .project-mini-card:hover {
          background: #f1f5f9;
          border-color: #667eea;
          box-shadow: 0 2px 6px rgba(102, 126, 234, 0.15);
        }

        .project-mini-thumbnail {
          width: 80px;
          height: 60px;
          flex-shrink: 0;
          border-radius: 4px;
          overflow: hidden;
          background: #e5e7eb;
        }

        .project-mini-thumbnail img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          object-position: top;
        }

        .thumbnail-placeholder-mini {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f3f4f6;
        }

        .thumbnail-placeholder-mini span {
          font-size: 10px;
          color: #9ca3af;
        }

        .project-mini-info {
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 4px;
          overflow: hidden;
          flex: 1;
        }

        .project-mini-header {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .project-status-badge-mini {
          padding: 2px 6px;
          border-radius: 8px;
          font-size: 10px;
          font-weight: 500;
        }

        .package-badge-mini {
          font-size: 10px;
          font-weight: 600;
        }

        .project-domain-mini {
          font-size: 12px;
          color: #374151;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-weight: 500;
        }

        .versions-count-mini {
          font-size: 11px;
          color: #6b7280;
        }

        .btn-manage-mini {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 28px;
          height: 28px;
          border: none;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          transition: all 0.2s ease;
        }

        .btn-manage-mini:hover {
          background: #667eea;
          transform: scale(1.1);
        }

        .empty-projects {
          text-align: center;
          padding: 24px 16px;
          color: #9ca3af;
        }

        .empty-projects p {
          margin: 0 0 4px;
          font-size: 14px;
        }

        .empty-projects .hint {
          font-size: 12px;
          color: #9ca3af;
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

        @media (max-width: 1200px) {
          .detail-grid {
            grid-template-columns: 350px 1fr;
          }

          .detail-grid > .projects-card {
            grid-column: 1;
            grid-row: 2;
          }

          .detail-grid > .activities-card {
            grid-row: 1 / span 2;
          }
        }

        @media (max-width: 900px) {
          .detail-grid {
            grid-template-columns: 1fr;
          }

          .detail-grid > .info-card,
          .detail-grid > .activities-card,
          .detail-grid > .projects-card {
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

          .test-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            color: white;
            border-radius: 9999px;
            font-size: 0.625rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
            animation: pulse 2s infinite;
          }

          @keyframes pulse {
            0% {
              transform: scale(1);
              opacity: 1;
            }
            50% {
              transform: scale(1.05);
              opacity: 0.9;
            }
            100% {
              transform: scale(1);
              opacity: 1;
            }
          }
        </style>
      </div>
    )
    }
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
      </style>
    </div>
  )
}
