'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import ApiClient from '../../../lib/api'
import { useAuth } from '../../../context/AuthContext'
import { useToast } from '../../../context/ToastContext'


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
  contact_person: string | null
  contact_name: string | null
}

interface CRMStats {
  total_leads: number
  new_leads: number
  calling: number
  interested: number
  offer_sent: number
  won: number
  lost: number
  dnc: number
  follow_ups_today: number
}

const STATUS_CONFIG: Record<string, { color: string; bg: string }> = {
  new: { color: '#3b82f6', bg: '#dbeafe' },
  calling: { color: '#eab308', bg: '#fef9c3' },
  interested: { color: '#f97316', bg: '#ffedd5' },
  offer_sent: { color: '#8b5cf6', bg: '#ede9fe' },
  won: { color: '#22c55e', bg: '#dcfce7' },
  lost: { color: '#6b7280', bg: '#f3f4f6' },
  dnc: { color: '#ef4444', bg: '#fee2e2' },
}

function CRMPageContent() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const { showToast } = useToast()
  const t = useTranslations('crm')
  const tc = useTranslations('common')
  const filterParam = searchParams.get('filter')

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      new: t('statusNew'),
      calling: t('statusCalling'),
      interested: t('statusInterested'),
      offer_sent: t('statusOfferSent'),
      won: t('statusWon'),
      lost: t('statusLost'),
      dnc: t('statusDnc'),
    }
    return labels[status] || status
  }

  const [businesses, setBusinesses] = useState<Business[]>([])
  const [stats, setStats] = useState<CRMStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [followUpFilter, setFollowUpFilter] = useState(filterParam === 'followup')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const limit = 20

  // Update followUpFilter when URL param changes
  useEffect(() => {
    setFollowUpFilter(filterParam === 'followup')
    setPage(1)
  }, [filterParam])

  // Auto-open new lead modal when action=new
  useEffect(() => {
    if (searchParams.get('action') === 'new') {
      openNewModal()
      // Clean URL to remove action parameter
      router.replace('/dashboard/crm')
    }
  }, [searchParams])

  // Modal states
  const [showNewModal, setShowNewModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState<Business | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    ico: '',
    phone: '',
    email: '',
    address: '',
    notes: '',
    status_crm: 'new',
    next_follow_up_at: '',
    contact_person: '', // Zpětná kompatibilita
    contact_name: '', // Nové pole
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isLoading, isAuthenticated, router])

  const fetchData = async () => {
    try {
      setLoading(true)

      // Build API params
      const apiParams: any = {
        search: search || undefined,
        status_crm: statusFilter || undefined,
        page,
        limit,
      }

      // Add follow-up filter if active (today's date)
      if (followUpFilter) {
        const today = new Date().toISOString().split('T')[0]
        apiParams.next_follow_up_at_before = today
      }

      const [businessesRes, statsRes] = await Promise.all([
        ApiClient.getBusinesses(apiParams),
        ApiClient.getCRMStats(),
      ])
      setBusinesses(businessesRes.items)
      setTotal(businessesRes.total)
      setStats(statsRes)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('loadError'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchData()
    }
  }, [isAuthenticated, search, statusFilter, followUpFilter, page])

  const clearFollowUpFilter = () => {
    setFollowUpFilter(false)
    router.push('/dashboard/crm')
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchData()
  }

  const openNewModal = () => {
    setFormData({
      name: '',
      ico: '',
      phone: '',
      email: '',
      address: '',
      notes: '',
      status_crm: 'new',
      next_follow_up_at: '',
      contact_person: '',
      contact_name: '',
    })
    setShowNewModal(true)
  }

  const openEditModal = (business: Business) => {
    setFormData({
      name: business.name,
      ico: (business as any).ico || '',
      phone: business.phone || '',
      email: business.email || '',
      address: business.address || '',
      notes: business.notes || '',
      status_crm: business.status_crm,
      next_follow_up_at: business.next_follow_up_at ? business.next_follow_up_at.split('T')[0] : '',
      contact_person: business.contact_person || '',
      contact_name: business.contact_name || '',
    })
    setShowEditModal(business)
  }

  const handleFillFromARES = async () => {
    if (!formData.ico || formData.ico.length !== 8) {
      showToast(t('aresInvalidIco'), 'warning')
      return
    }

    setLoading(true)
    try {
      const aresData = await ApiClient.getCompanyFromARES(formData.ico)

      // Fill form with ARES data
      setFormData(prev => ({
        ...prev,
        name: aresData.obchodniJmeno || prev.name,
        address: aresData.sidlo?.textovaAdresa || prev.address,
        // You can add more fields here as needed
      }))

      showToast(t('aresLoaded'), 'success')
    } catch (error: any) {
      console.error('ARES API error:', error)
      showToast(t('aresError', { detail: error.response?.data?.detail || error.message }), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!formData.name.trim()) {
      setError(t('companyRequired'))
      return
    }

    setSaving(true)
    setError('')

    try {
      const data = {
        ...formData,
        ico: formData.ico || null,
        next_follow_up_at: formData.next_follow_up_at || null,
      }

      if (showEditModal) {
        await ApiClient.updateBusiness(showEditModal.id, data)
      } else {
        await ApiClient.createBusiness(data)
      }

      setShowNewModal(false)
      setShowEditModal(null)
      fetchData()
    } catch (err: any) {
      setError(err.response?.data?.detail || t('saveError'))
    } finally {
      setSaving(false)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('cs-CZ')
  }

  const isOverdue = (dateStr: string | null) => {
    if (!dateStr) return false
    return new Date(dateStr) < new Date()
  }

  if (isLoading || !user) {
    return <div className="loading">{tc('loading')}</div>
  }

  return (
    <div className="crm-page">
      <header className="crm-header">
        <div className="header-left">
          <h1>{followUpFilter ? t('followUpsTitle') : t('title')}</h1>
        </div>
        <div className="header-right">
          <button className="btn-new" onClick={openNewModal}>{t('newLead')}</button>
        </div>
      </header>

      {/* Stats */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{stats.total_leads}</span>
            <span className="stat-label">{t('total')}</span>
          </div>
          <div className="stat-card highlight">
            <span className="stat-value">{stats.follow_ups_today}</span>
            <span className="stat-label">{t('today')}</span>
          </div>
          <div className="stat-card" style={{ borderColor: STATUS_CONFIG.new.color }}>
            <span className="stat-value">{stats.new_leads}</span>
            <span className="stat-label">{t('new')}</span>
          </div>
          <div className="stat-card" style={{ borderColor: STATUS_CONFIG.calling.color }}>
            <span className="stat-value">{stats.calling}</span>
            <span className="stat-label">{t('calling')}</span>
          </div>
          <div className="stat-card" style={{ borderColor: STATUS_CONFIG.interested.color }}>
            <span className="stat-value">{stats.interested}</span>
            <span className="stat-label">{t('interested')}</span>
          </div>
          <div className="stat-card" style={{ borderColor: STATUS_CONFIG.won.color }}>
            <span className="stat-value">{stats.won}</span>
            <span className="stat-label">{t('won')}</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder={t('searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn-search">{tc('search')}</button>
        </form>

        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="status-filter"
        >
          <option value="">{t('allStatuses')}</option>
          <option value="new">{t('statusNew')}</option>
          <option value="calling">{t('statusCalling')}</option>
          <option value="interested">{t('statusInterested')}</option>
          <option value="offer_sent">{t('statusOfferSent')}</option>
          <option value="won">{t('statusWon')}</option>
          <option value="lost">{t('statusLost')}</option>
          <option value="dnc">{t('statusDnc')}</option>
        </select>
      </div>

      {/* Active filter indicator */}
      {followUpFilter && (
        <div className="filter-indicator">
          <span className="filter-badge">
            📋 {t('followUpFilterActive')}
          </span>
          <button className="btn-clear-filter" onClick={clearFollowUpFilter}>
            × {t('clearFilter')}
          </button>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {/* Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-table">{tc('loading')}</div>
        ) : businesses.length === 0 ? (
          <div className="empty-state">
            <p>{t('noLeadsFound')}</p>
            <button className="btn-new" onClick={openNewModal}>{t('createFirstLead')}</button>
          </div>
        ) : (
          <table className="crm-table">
            <thead>
              <tr>
                <th>{t('company')}</th>
                <th>{t('phone')}</th>
                <th>{t('status')}</th>
                <th>{t('followUp')}</th>
                <th>{t('assignedTo')}</th>
                <th>{tc('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((b) => (
                <tr 
                  key={b.id} 
                  className={['won', 'lost', 'dnc'].includes(b.status_crm) ? 'closed clickable-row' : 'clickable-row'}
                  onClick={() => router.push(`/dashboard/crm/${b.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td>
                    <strong>{b.name}</strong>
                    {b.email && <div className="sub-text">{b.email}</div>}
                  </td>
                  <td>
                    {b.phone ? (
                      <a href={`tel:${b.phone}`} className="phone-link">{b.phone}</a>
                    ) : '-'}
                  </td>
                  <td>
                    <span
                      className="status-badge"
                      style={{
                        color: STATUS_CONFIG[b.status_crm]?.color || '#666',
                        backgroundColor: STATUS_CONFIG[b.status_crm]?.bg || '#f5f5f5',
                      }}
                    >
                      {getStatusLabel(b.status_crm)}
                    </span>
                  </td>
                  <td className={isOverdue(b.next_follow_up_at) ? 'overdue' : ''}>
                    {formatDate(b.next_follow_up_at)}
                  </td>
                  <td>{b.owner_seller_name || '-'}</td>
                  <td className="actions">
<button
                      className="btn-small"
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/dashboard/crm/${b.id}`);
                      }}
                    >
                      {tc('detail')}
                    </button>
<button
                      className="btn-small btn-edit"
                      onClick={(e) => {
                        e.stopPropagation();
                        openEditModal(b);
                      }}
                    >
                      {tc('edit')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="pagination">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            {tc('previous')}
          </button>
          <span>{tc('pageOf', { page, total: Math.ceil(total / limit) })}</span>
          <button
            disabled={page * limit >= total}
            onClick={() => setPage(p => p + 1)}
          >
            {tc('next')}
          </button>
        </div>
      )}

      {/* New/Edit Modal */}
      {(showNewModal || showEditModal) && (
        <div className="modal-overlay" onClick={() => { setShowNewModal(false); setShowEditModal(null); }}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{showEditModal ? t('editLead') : t('newLeadTitle')}</h2>

             <div className="form-row">
               <div className="form-group">
                 <label>{t('ico')}</label>
                 <div style={{ display: 'flex', gap: '8px' }}>
                   <input
                     type="text"
                     value={formData.ico}
                     onChange={(e) => setFormData({ ...formData, ico: e.target.value })}
                     placeholder="12345678"
                     maxLength={8}
                     style={{ flex: 1, minWidth: '120px' }}
                   />
                   <button
                     type="button"
                     onClick={handleFillFromARES}
                     disabled={!formData.ico || loading}
                     className="ares-button"
                   >
                     {loading ? (
                       <>
                         <div className="spinner"></div>
                         {t('aresLoading')}
                       </>
                     ) : (
                       <>
                         <span className="icon">🔍</span>
                         ARES
                       </>
                     )}
                   </button>
                 </div>
               </div>
               <div className="form-group">
                 <label>{t('companyName')}</label>
                 <input
                   type="text"
                   value={formData.name}
                   onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                   placeholder="ABC s.r.o."
                 />
               </div>
             </div>

            <div className="form-row">
               <div className="form-group">
                 <label>{t('phone')}</label>
                 <input
                   type="tel"
                   value={formData.phone}
                   onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                   placeholder="+420 777 123 456"
                 />
               </div>
               <div className="form-group">
                 <label>{t('email')}</label>
                 <input
                   type="email"
                   value={formData.email}
                   onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                   placeholder="info@firma.cz"
                 />
               </div>
               <div className="form-group">
                 <label>{t('contactPerson')}</label>
                 <input
                   type="text"
                   value={formData.contact_name}
                   onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                   placeholder={t('contactNamePlaceholder')}
                 />
               </div>
            </div>

            <div className="form-group">
              <label>{t('address')}</label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="Ulice 123, Praha"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>{t('status')}</label>
                <select
                  value={formData.status_crm}
                  onChange={(e) => setFormData({ ...formData, status_crm: e.target.value })}
                >
                  {Object.keys(STATUS_CONFIG).map((key) => (
                    <option key={key} value={key}>{getStatusLabel(key)}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>{t('followUp')}</label>
                <input
                  type="date"
                  value={formData.next_follow_up_at}
                  onChange={(e) => setFormData({ ...formData, next_follow_up_at: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>{t('notes')}</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder={t('notesPlaceholder')}
                rows={3}
              />
            </div>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => { setShowNewModal(false); setShowEditModal(null); }}
              >
                {tc('cancel')}
              </button>
              <button
                className="btn-primary"
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? tc('saving') : tc('save')}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .crm-page {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .crm-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .header-left h1 {
          margin: 0;
          font-size: 24px;
          color: #1a1a2e;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .user-info {
          color: #666;
          font-size: 14px;
        }

        .btn-back {
          background: none;
          border: 1px solid #ddd;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          color: #666;
        }

        .btn-back:hover {
          background: #f5f5f5;
        }

        .btn-new {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-new:hover {
          opacity: 0.9;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 12px;
          margin-bottom: 24px;
        }

        .stat-card {
          background: white;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          padding: 16px;
          text-align: center;
        }

        .stat-card.highlight {
          border-color: #667eea;
          background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
        }

        .stat-value {
          display: block;
          font-size: 28px;
          font-weight: 700;
          color: #1a1a2e;
        }

        .stat-label {
          font-size: 12px;
          color: #666;
          text-transform: uppercase;
        }

        .filters {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }

        .search-form {
          display: flex;
          gap: 8px;
          flex: 1;
          min-width: 200px;
        }

        .search-input {
          flex: 1;
          padding: 10px 14px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .btn-search {
          padding: 10px 20px;
          background: #f5f5f5;
          border: 1px solid #ddd;
          border-radius: 6px;
          cursor: pointer;
        }

        .status-filter {
          padding: 10px 14px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
          min-width: 180px;
        }

        .filter-indicator {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
          border: 1px solid #f59e0b;
          border-radius: 8px;
          margin-bottom: 16px;
        }

        .filter-badge {
          font-weight: 500;
          color: #92400e;
        }

        .btn-clear-filter {
          padding: 6px 12px;
          background: white;
          border: 1px solid #f59e0b;
          border-radius: 6px;
          color: #92400e;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-clear-filter:hover {
          background: #fffbeb;
          border-color: #d97706;
        }

        .error-message {
          background: #fee2e2;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 6px;
          margin-bottom: 16px;
        }

        .table-container {
          background: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .crm-table {
          width: 100%;
          border-collapse: collapse;
        }

        .crm-table th,
        .crm-table td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }

        .crm-table th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
          font-size: 13px;
          text-transform: uppercase;
        }

        .crm-table tr:hover {
          background: #f9fafb;
        }

        .crm-table tr.closed {
          opacity: 0.6;
        }

        .sub-text {
          font-size: 12px;
          color: #666;
        }

        .phone-link {
          color: #667eea;
          text-decoration: none;
        }

        .phone-link:hover {
          text-decoration: underline;
        }

        .status-badge {
          display: inline-block;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .overdue {
          color: #dc2626;
          font-weight: 600;
        }

        .actions {
          display: flex;
          gap: 8px;
        }

        .btn-small {
          padding: 6px 12px;
          font-size: 12px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-small:hover {
          background: #f5f5f5;
        }

        .btn-edit {
          color: #667eea;
          border-color: #667eea;
        }

        .loading-table,
        .empty-state {
          padding: 60px 20px;
          text-align: center;
          color: #666;
        }

        .empty-state .btn-new {
          margin-top: 16px;
        }

        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 16px;
          padding: 20px;
        }

        .pagination button {
          padding: 8px 16px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
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
          max-height: 90vh;
          overflow-y: auto;
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

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
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

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          font-size: 18px;
          color: #666;
        }

        /* Modern Button Animations - 2026 Best Practices */
        .ares-button {
          padding: 10px 16px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          position: relative;
          overflow: hidden;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          transform: translateY(0);
        }

        .ares-button::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          transition: left 0.5s;
        }

        .ares-button:hover:not(:disabled)::before {
          left: 100%;
        }

        .ares-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
          background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
        }

        .ares-button:active:not(:disabled) {
          transform: translateY(0);
          transition-duration: 0.1s;
        }

        .ares-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .icon {
          font-size: 16px;
          transition: transform 0.3s ease;
        }

        .ares-button:hover:not(:disabled) .icon {
          transform: scale(1.1) rotate(5deg);
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        /* Enhanced submit buttons */
        .btn-primary, .btn-secondary {
          position: relative;
          overflow: hidden;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-primary::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 0;
          height: 0;
          background: rgba(255,255,255,0.2);
          border-radius: 50%;
          transform: translate(-50%, -50%);
          transition: width 0.6s, height 0.6s;
        }

        .btn-primary:hover:not(:disabled)::before {
          width: 300px;
          height: 300px;
        }

        .btn-secondary:hover {
          background: #f0f0f0;
          transform: translateY(-1px);
        }

        /* Form input focus animations */
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
          transform: scale(1.02);
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
          transition: all 0.3s ease;
        }

        /* Loading table animation */
        .loading-table {
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        /* Status badge hover */
        .status-badge {
          transition: transform 0.2s ease;
        }

        .status-badge:hover {
          transform: scale(1.05);
        }

        /* Modal entrance animation */
        .modal {
          animation: modalSlideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes modalSlideIn {
          from {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @media (max-width: 768px) {
          .crm-header {
            flex-direction: column;
            gap: 16px;
            align-items: flex-start;
          }

          .filters {
            flex-direction: column;
          }

          .form-row {
            grid-template-columns: 1fr;
          }

          .crm-table {
            font-size: 14px;
          }

.actions {
            flex-direction: column;
          }

          .clickable-row:hover {
            background: #f3f4f6 !important;
          }

          .crm-table .actions {
            display: none;
          }
        }
      `}</style>
    </div>
  )
}

// Wrap with Suspense for useSearchParams
export default function CRMPage() {
  const tc = useTranslations('common')
  return (
    <Suspense fallback={<div className="loading">{tc('loading')}</div>}>
      <CRMPageContent />
    </Suspense>
  )
}
