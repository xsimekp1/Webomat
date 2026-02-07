'use client'

import { useRouter, useParams } from 'next/navigation'
import { formatCurrency, formatDate } from '../../../../lib/utils'

import { useEffect, useState } from 'react'
import ApiClient from '../../../../lib/api'
import { useAuth } from '../../../../context/AuthContext'
import { useToast } from '../../../../context/ToastContext'
import { useLanguage } from '../../../../context/LanguageContext'
import { useTranslations } from 'next-intl'



export default function InvoiceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const invoiceId = params.invoiceId as string
  const locale = (params.locale as string) || 'cs'

  const [invoice, setInvoice] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  useEffect(() => {
    if (invoiceId) {
      loadInvoice()
    }
  }, [invoiceId])

  const loadInvoice = async () => {
    try {
      setLoading(true)
      const data = await ApiClient.getInvoiceDetail(invoiceId)
      setInvoice(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při načítání faktury')
    } finally {
      setLoading(false)
    }
  }

  const updateInvoiceStatus = async (newStatus: 'draft' | 'issued' | 'paid' | 'overdue' | 'cancelled', paidDate?: string) => {
    if (!invoice || user?.role !== 'admin') {
      showToast('Pouze admin může měnit status faktury', 'error')
      return
    }

    try {
      setUpdating(true)
      await ApiClient.updateInvoiceStatus(invoice.id, {
        status: newStatus,
        paid_date: paidDate
      })
      
      await loadInvoice()
      showToast(`Faktura označena jako ${newStatus === 'paid' ? 'zaplacená' : newStatus}`, 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při aktualizaci faktury', 'error')
    } finally {
      setUpdating(false)
    }
  }

  const handleSubmitForApproval = async () => {
    if (!invoice) return
    try {
      setSubmitting(true)
      await ApiClient.submitInvoiceForApproval(invoice.id)
      await loadInvoice()
      showToast('Faktura odeslána ke schválení', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při odesílání ke schválení', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApprove = async () => {
    if (!invoice) return
    try {
      setApproving(true)
      await ApiClient.approveInvoice(invoice.id)
      await loadInvoice()
      showToast('Faktura byla schválena', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při schvalování', 'error')
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!invoice || !rejectReason.trim()) {
      showToast('Zadejte důvod zamítnutí', 'error')
      return
    }
    try {
      setRejecting(true)
      await ApiClient.rejectInvoice(invoice.id, rejectReason.trim())
      setShowRejectModal(false)
      setRejectReason('')
      await loadInvoice()
      showToast('Faktura byla zamítnuta', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při zamítání', 'error')
    } finally {
      setRejecting(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return '#666'
      case 'pending_approval': return '#eab308'
      case 'issued': return '#2563eb'
      case 'paid': return '#16a34a'
      case 'overdue': return '#dc2626'
      case 'cancelled': return '#6b7280'
      default: return '#666'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'Návrh'
      case 'pending_approval': return 'Čeká na schválení'
      case 'issued': return 'Vystaveno'
      case 'paid': return 'Zaplaceno'
      case 'overdue': return 'Po splatnosti'
      case 'cancelled': return 'Stornováno'
      default: return status
    }
  }

  const getPaymentTypeLabel = (type: string) => {
    switch (type) {
      case 'setup': return 'Jednorázový poplatek'
      case 'monthly': return 'Měsíční poplatek'
      case 'other': return 'Ostatní'
      default: return type
    }
  }

  const handleDownloadPdf = async () => {
    if (!invoice) return

    try {
      setDownloadingPdf(true)
      const pdfUrl = await ApiClient.downloadInvoicePdf(invoice.id)
      window.open(pdfUrl, '_blank')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Chyba při stahování PDF', 'error')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Načítám fakturu...</h1>
        </div>
      </div>
    )
  }

  if (error || !invoice) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Chyba</h1>
        </div>
        <div className="card">
          <p>{error || 'Faktura nebyla nalezena'}</p>
          <button className="btn-primary" onClick={() => router.back()}>
            Zpět
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Detail faktury</h1>
        <div className="page-header-actions">
          <button
            className="btn-primary"
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
          >
            {downloadingPdf ? 'Stahuji...' : 'Stáhnout PDF'}
          </button>
          <button className="btn-secondary" onClick={() => router.back()}>
            Zpět
          </button>
        </div>
      </div>

      <div className="wip-banner">
        <span className="wip-icon">&#9432;</span>
        <span>
          {locale === 'en'
            ? 'PDF generation: WIP — a placeholder PDF will be generated. Full invoice template coming soon.'
            : 'Generování PDF: WIP — vygeneruje se zástupné PDF. Plná šablona faktury bude brzy dostupná.'}
        </span>
      </div>

      <div className="card invoice-detail-card">
        <div className="invoice-header">
          <div className="invoice-number">
            <h2>Faktura #{invoice.invoice_number}</h2>
            <span 
              className="status-badge"
              style={{ 
                color: getStatusColor(invoice.status),
                backgroundColor: `${getStatusColor(invoice.status)}20`
              }}
            >
              {getStatusLabel(invoice.status)}
            </span>
          </div>
          <div className="invoice-amount">
            <div className="total-amount">{formatCurrency(invoice.amount_total)}</div>
            <div className="vat-info">včetně DPH</div>
          </div>
        </div>

        <div className="invoice-info">
          <div className="info-section">
            <h3>Informace o faktuře</h3>
            <div className="info-grid">
              <div className="info-item">
                <label>Klient:</label>
                <span>{invoice.business_name}</span>
              </div>
              <div className="info-item">
                <label>Číslo faktury:</label>
                <span>{invoice.invoice_number}</span>
              </div>
              <div className="info-item">
                <label>Typ platby:</label>
                <span>{getPaymentTypeLabel(invoice.payment_type)}</span>
              </div>
              <div className="info-item">
                <label>Men:</label>
                <span>{invoice.currency}</span>
              </div>
              <div className="info-item">
                <label>Datum vystavení:</label>
                <span>{formatDate(invoice.issue_date)}</span>
              </div>
              <div className="info-item">
                <label>Datum splatnosti:</label>
                <span>{formatDate(invoice.due_date)}</span>
              </div>
              {invoice.paid_date && (
                <div className="info-item">
                  <label>Datum zaplacení:</label>
                  <span>{formatDate(invoice.paid_date)}</span>
                </div>
              )}
              {invoice.variable_symbol && (
                <div className="info-item">
                  <label>Variabilní symbol:</label>
                  <span>{invoice.variable_symbol}</span>
                </div>
              )}
            </div>
          </div>

          <div className="info-section">
            <h3>Finanční detaily</h3>
            <div className="price-breakdown">
              <div className="price-row">
                <span>Částka bez DPH:</span>
                <span>{formatCurrency(invoice.amount_without_vat)}</span>
              </div>
              {invoice.vat_amount && (
                <div className="price-row">
                  <span>DPH ({invoice.vat_rate}%):</span>
                  <span>{formatCurrency(invoice.vat_amount)}</span>
                </div>
              )}
              <div className="price-row total">
                <span>Celkem:</span>
                <span>{formatCurrency(invoice.amount_total)}</span>
              </div>
            </div>
          </div>
        </div>

        {invoice.description && (
          <div className="info-section">
            <h3>Popis</h3>
            <p>{invoice.description}</p>
          </div>
        )}

        {/* Show rejection reason if invoice was rejected */}
        {invoice.rejected_reason && (
          <div className="info-section rejection-section">
            <h3>Důvod zamítnutí</h3>
            <p className="rejection-reason">{invoice.rejected_reason}</p>
          </div>
        )}

        {/* Actions for Sales - Submit for approval */}
        {invoice.status === 'draft' && (
          <div className="invoice-actions">
            <h3>Akce</h3>
            <div className="action-buttons">
              <button
                className="btn-primary"
                onClick={handleSubmitForApproval}
                disabled={submitting}
              >
                {submitting ? 'Odesílám...' : 'Odeslat ke schválení'}
              </button>
            </div>
            {invoice.rejected_reason && (
              <p className="action-hint">
                Faktura byla vrácena k úpravě. Po opravě ji můžete znovu odeslat ke schválení.
              </p>
            )}
          </div>
        )}

        {/* Status info for pending approval (sales view) */}
        {invoice.status === 'pending_approval' && user?.role !== 'admin' && (
          <div className="invoice-actions">
            <h3>Stav</h3>
            <p className="pending-info">
              Faktura čeká na schválení administrátorem.
            </p>
          </div>
        )}

        {/* Admin actions */}
        {user?.role === 'admin' && (
          <div className="invoice-actions">
            <h3>Admin akce</h3>
            <div className="action-buttons">
              {invoice.status === 'pending_approval' && (
                <>
                  <button
                    className="btn-success"
                    onClick={handleApprove}
                    disabled={approving}
                  >
                    {approving ? 'Schvaluji...' : 'Schválit'}
                  </button>
                  <button
                    className="btn-danger"
                    onClick={() => setShowRejectModal(true)}
                  >
                    Zamítnout
                  </button>
                </>
              )}
              {invoice.status === 'draft' && (
                <button
                  className="btn-primary"
                  onClick={() => updateInvoiceStatus('issued')}
                  disabled={updating}
                >
                  {updating ? 'Aktualizuji...' : 'Vystavit přímo'}
                </button>
              )}
              {(invoice.status === 'issued' || invoice.status === 'overdue') && (
                <button
                  className="btn-primary"
                  onClick={() => updateInvoiceStatus('paid', new Date().toISOString().split('T')[0])}
                  disabled={updating}
                >
                  {updating ? 'Aktualizuji...' : 'Označit jako zaplaceno'}
                </button>
              )}
              {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                <button
                  className="btn-danger"
                  onClick={() => updateInvoiceStatus('cancelled')}
                  disabled={updating}
                >
                  Stornovat
                </button>
              )}
            </div>
          </div>
        )}

        <div className="invoice-meta">
          <small>
            Vytvořeno: {formatDate(invoice.created_at)}
            {invoice.updated_at && ` • Aktualizováno: ${formatDate(invoice.updated_at)}`}
          </small>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Zamítnout fakturu</h2>
            <p>Zamítnout fakturu: <strong>#{invoice.invoice_number}</strong></p>
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
                  setShowRejectModal(false)
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
        .wip-banner {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          background: #fefce8;
          border: 1px solid #fde68a;
          border-radius: 0.5rem;
          padding: 0.75rem 1rem;
          margin-bottom: 1rem;
          color: #92400e;
          font-size: 0.875rem;
        }

        .wip-icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .invoice-detail-card {
          max-width: 800px;
        }

        .invoice-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e5e7eb;
        }

        .invoice-number {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .invoice-number h2 {
          margin: 0;
          font-size: 1.5rem;
          color: #111827;
        }

        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .invoice-amount {
          text-align: right;
        }

        .total-amount {
          font-size: 1.875rem;
          font-weight: 700;
          color: #111827;
        }

        .vat-info {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .invoice-info {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
          margin-bottom: 2rem;
        }

        .info-section {
          margin-bottom: 2rem;
        }

        .info-section h3 {
          margin: 0 0 1rem 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: #111827;
        }

        .info-grid {
          display: grid;
          gap: 0.75rem;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
        }

        .info-item label {
          font-weight: 500;
          color: #374151;
        }

        .info-item span {
          color: #6b7280;
        }

        .price-breakdown {
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          padding: 1rem;
        }

        .price-row {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem 0;
        }

        .price-row.total {
          border-top: 1px solid #e5e7eb;
          font-weight: 600;
          color: #111827;
          padding-top: 1rem;
          margin-top: 0.5rem;
        }

        .invoice-actions {
          border-top: 1px solid #e5e7eb;
          padding-top: 1.5rem;
          margin-top: 2rem;
        }

        .invoice-actions h3 {
          margin: 0 0 1rem 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: #111827;
        }

        .action-buttons {
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }

        .action-hint {
          margin-top: 0.75rem;
          color: #6b7280;
          font-size: 0.875rem;
        }

        .pending-info {
          color: #eab308;
          font-weight: 500;
        }

        .rejection-section {
          background: #fef2f2;
          padding: 1rem;
          border-radius: 0.5rem;
          border: 1px solid #fecaca;
        }

        .rejection-reason {
          color: #dc2626;
          font-weight: 500;
        }

        .btn-success {
          background: #22c55e;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }

        .btn-success:hover {
          background: #16a34a;
        }

        .btn-success:disabled {
          opacity: 0.6;
          cursor: not-allowed;
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

        .invoice-meta {
          margin-top: 2rem;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .invoice-meta small {
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .invoice-header {
            flex-direction: column;
            gap: 1rem;
            align-items: flex-start;
          }

          .invoice-amount {
            text-align: left;
          }

          .invoice-info {
            grid-template-columns: 1fr;
            gap: 1.5rem;
          }

          .action-buttons {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  )
}
