'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import ApiClient from '../../lib/api'
import { formatCurrency, formatDate } from '../../lib/utils'

interface AdminInvoice {
  id: string
  invoice_number: string
  business_id: string
  business_name: string | null
  seller_id: string | null
  seller_name: string | null
  amount_total: number
  status: string
  issue_date: string
  due_date: string
  paid_date: string | null
  payment_type: string
  rejected_reason: string | null
  created_at: string | null
}

interface AdminInvoicesResponse {
  items: AdminInvoice[]
  total: number
  page: number
  limit: number
}

const STATUS_OPTIONS = [
  { value: '', label: 'Vše' },
  { value: 'pending_approval', label: 'Čeká na schválení' },
  { value: 'draft', label: 'Návrh' },
  { value: 'issued', label: 'Vystaveno' },
  { value: 'paid', label: 'Zaplaceno' },
  { value: 'overdue', label: 'Po splatnosti' },
  { value: 'cancelled', label: 'Stornováno' },
]

export default function AdminInvoicesPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const router = useRouter()

  const [invoices, setInvoices] = useState<AdminInvoice[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters
  const [statusFilter, setStatusFilter] = useState('pending_approval')
  const [page, setPage] = useState(1)
  const limit = 20

  // Reject modal
  const [rejectModal, setRejectModal] = useState<{ invoiceId: string; invoiceNumber: string } | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [rejecting, setRejecting] = useState(false)

  // Action loading states
  const [approving, setApproving] = useState<string | null>(null)
  const [markingPaid, setMarkingPaid] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/')
      } else if (user?.role !== 'admin') {
        router.push('/dashboard')
      }
    }
  }, [isLoading, isAuthenticated, user, router])

  useEffect(() => {
    if (user?.role === 'admin') {
      loadInvoices()
    }
  }, [user, statusFilter, page])

  const loadInvoices = async () => {
    try {
      setLoading(true)
      const response: AdminInvoicesResponse = await ApiClient.getAdminInvoices({
        status: statusFilter || undefined,
        page,
        limit,
      })
      setInvoices(response.items)
      setTotal(response.total)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodařilo se načíst faktury')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (invoiceId: string) => {
    try {
      setApproving(invoiceId)
      await ApiClient.approveInvoice(invoiceId)
      showToast('Faktura byla schválena', 'success')
      loadInvoices()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při schvalování', 'error')
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async () => {
    if (!rejectModal || !rejectReason.trim()) {
      showToast('Zadejte důvod zamítnutí', 'error')
      return
    }

    try {
      setRejecting(true)
      await ApiClient.rejectInvoice(rejectModal.invoiceId, rejectReason.trim())
      showToast('Faktura byla zamítnuta', 'success')
      setRejectModal(null)
      setRejectReason('')
      loadInvoices()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při zamítání', 'error')
    } finally {
      setRejecting(false)
    }
  }

  const handleMarkPaid = async (invoiceId: string) => {
    try {
      setMarkingPaid(invoiceId)
      await ApiClient.updateInvoiceStatus(invoiceId, {
        status: 'paid',
        paid_date: new Date().toISOString().split('T')[0]
      })
      showToast('Faktura označena jako zaplacená', 'success')
      loadInvoices()
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při aktualizaci', 'error')
    } finally {
      setMarkingPaid(null)
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      draft: 'Návrh',
      pending_approval: 'Čeká na schválení',
      issued: 'Vystaveno',
      paid: 'Zaplaceno',
      overdue: 'Po splatnosti',
      cancelled: 'Stornováno',
    }
    return labels[status] || status
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#6b7280',
      pending_approval: '#eab308',
      issued: '#3b82f6',
      paid: '#22c55e',
      overdue: '#ef4444',
      cancelled: '#6b7280',
    }
    return colors[status] || '#6b7280'
  }

  const getPaymentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      setup: 'Jednorázový',
      monthly: 'Měsíční',
      other: 'Ostatní',
    }
    return labels[type] || type
  }

  const totalPages = Math.ceil(total / limit)

  if (isLoading || !user) {
    return <div className="loading">Načítám...</div>
  }

  if (user.role !== 'admin') {
    return null
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <button onClick={() => router.push('/dashboard')} className="btn-back">
          Zpět na dashboard
        </button>
        <h1>Správa faktur</h1>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <main className="admin-main">
        {/* Filters */}
        <div className="filters">
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-info">
            Celkem: <strong>{total}</strong> faktur
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="loading">Načítám faktury...</div>
        ) : invoices.length === 0 ? (
          <div className="empty-state">
            <p>Žádné faktury nenalezeny</p>
          </div>
        ) : (
          <>
            <table className="invoices-table">
              <thead>
                <tr>
                  <th>Č. faktury</th>
                  <th>Klient</th>
                  <th>Obchodník</th>
                  <th>Částka</th>
                  <th>Status</th>
                  <th>Vystaveno</th>
                  <th>Splatnost</th>
                  <th>Akce</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td>
                      <a
                        href={`/dashboard/invoices/${inv.id}`}
                        className="invoice-link"
                        onClick={(e) => {
                          e.preventDefault()
                          router.push(`/dashboard/invoices/${inv.id}`)
                        }}
                      >
                        {inv.invoice_number}
                      </a>
                    </td>
                    <td>{inv.business_name || '-'}</td>
                    <td>{inv.seller_name || '-'}</td>
                    <td className="amount">{formatCurrency(inv.amount_total)}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          backgroundColor: `${getStatusColor(inv.status)}20`,
                          color: getStatusColor(inv.status),
                        }}
                      >
                        {getStatusLabel(inv.status)}
                      </span>
                      {inv.rejected_reason && (
                        <div className="rejection-reason" title={inv.rejected_reason}>
                          Důvod: {inv.rejected_reason.substring(0, 30)}...
                        </div>
                      )}
                    </td>
                    <td>{formatDate(inv.issue_date)}</td>
                    <td>{formatDate(inv.due_date)}</td>
                    <td className="actions">
                      {inv.status === 'pending_approval' && (
                        <>
                          <button
                            className="btn-small btn-success"
                            onClick={() => handleApprove(inv.id)}
                            disabled={approving === inv.id}
                          >
                            {approving === inv.id ? '...' : 'Schválit'}
                          </button>
                          <button
                            className="btn-small btn-danger"
                            onClick={() => setRejectModal({ invoiceId: inv.id, invoiceNumber: inv.invoice_number })}
                          >
                            Zamítnout
                          </button>
                        </>
                      )}
                      {(inv.status === 'issued' || inv.status === 'overdue') && (
                        <button
                          className="btn-small btn-primary"
                          onClick={() => handleMarkPaid(inv.id)}
                          disabled={markingPaid === inv.id}
                        >
                          {markingPaid === inv.id ? '...' : 'Zaplaceno'}
                        </button>
                      )}
                      <button
                        className="btn-small"
                        onClick={() => router.push(`/dashboard/invoices/${inv.id}`)}
                      >
                        Detail
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-page"
                >
                  Předchozí
                </button>
                <span className="page-info">
                  Stránka {page} z {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn-page"
                >
                  Další
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Reject Modal */}
      {rejectModal && (
        <div className="modal-overlay" onClick={() => setRejectModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Zamítnout fakturu</h2>
            <p>
              Zamítnout fakturu: <strong>{rejectModal.invoiceNumber}</strong>
            </p>
            <div className="field">
              <label htmlFor="rejectReason">Důvod zamítnutí *</label>
              <textarea
                id="rejectReason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Zadejte důvod zamítnutí..."
                rows={4}
              />
            </div>
            <div className="modal-actions">
              <button
                onClick={() => {
                  setRejectModal(null)
                  setRejectReason('')
                }}
                className="btn-secondary"
                disabled={rejecting}
              >
                Zrušit
              </button>
              <button
                onClick={handleReject}
                className="btn-danger"
                disabled={rejecting || !rejectReason.trim()}
              >
                {rejecting ? 'Zamítám...' : 'Zamítnout'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .admin-page {
          min-height: 100vh;
          background: #f5f5f5;
        }
        .admin-header {
          background: #1a1a2e;
          color: white;
          padding: 1rem 2rem;
          display: flex;
          align-items: center;
          gap: 2rem;
        }
        .admin-header h1 {
          margin: 0;
          font-size: 1.5rem;
        }
        .btn-back {
          background: transparent;
          border: 1px solid #fff;
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
        }
        .btn-back:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        .admin-main {
          padding: 2rem;
        }
        .alert {
          padding: 1rem;
          border-radius: 4px;
          margin: 1rem 2rem;
        }
        .alert-error {
          background: #fee;
          color: #c00;
          border: 1px solid #fcc;
        }

        /* Filters */
        .filters {
          display: flex;
          gap: 2rem;
          align-items: center;
          margin-bottom: 1.5rem;
          background: white;
          padding: 1rem 1.5rem;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .filter-group {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .filter-group label {
          font-weight: 500;
          color: #374151;
        }
        .filter-group select {
          padding: 0.5rem 1rem;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 0.95rem;
          min-width: 180px;
        }
        .filter-info {
          margin-left: auto;
          color: #6b7280;
        }

        /* Table */
        .invoices-table {
          width: 100%;
          background: white;
          border-collapse: collapse;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .invoices-table th,
        .invoices-table td {
          padding: 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }
        .invoices-table th {
          background: #f8f9fa;
          font-weight: 600;
        }
        .invoice-link {
          color: #3b82f6;
          text-decoration: none;
          font-weight: 500;
        }
        .invoice-link:hover {
          text-decoration: underline;
        }
        .amount {
          font-weight: 600;
          white-space: nowrap;
        }
        .status-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.85rem;
          font-weight: 500;
        }
        .rejection-reason {
          font-size: 0.75rem;
          color: #ef4444;
          margin-top: 4px;
          max-width: 150px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .actions {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .btn-small {
          padding: 0.4rem 0.8rem;
          font-size: 0.85rem;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          background: #6c757d;
          color: white;
          white-space: nowrap;
        }
        .btn-small:hover {
          background: #5a6268;
        }
        .btn-small:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .btn-primary {
          background: #3b82f6;
        }
        .btn-primary:hover {
          background: #2563eb;
        }
        .btn-danger {
          background: #dc3545;
        }
        .btn-danger:hover {
          background: #c82333;
        }
        .btn-success {
          background: #22c55e;
        }
        .btn-success:hover {
          background: #16a34a;
        }

        /* Pagination */
        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
          margin-top: 1.5rem;
        }
        .btn-page {
          padding: 0.5rem 1rem;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          cursor: pointer;
        }
        .btn-page:hover:not(:disabled) {
          background: #f3f4f6;
        }
        .btn-page:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .page-info {
          color: #6b7280;
        }

        /* Empty state */
        .empty-state {
          text-align: center;
          padding: 3rem;
          background: white;
          border-radius: 8px;
          color: #6b7280;
        }

        /* Modal */
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
          padding: 2rem;
          border-radius: 8px;
          max-width: 500px;
          width: 90%;
        }
        .modal h2 {
          margin-top: 0;
        }
        .field {
          margin: 1rem 0;
        }
        .field label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
        }
        .field textarea {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
          resize: vertical;
        }
        .modal-actions {
          display: flex;
          gap: 1rem;
          justify-content: flex-end;
          margin-top: 1.5rem;
        }
        .btn-secondary {
          background: #6c757d;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
        }
        .btn-secondary:hover {
          background: #5a6268;
        }
        .loading {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
      `}</style>
    </div>
  )
}
