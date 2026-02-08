'use client'

import { useRouter, useParams } from 'next/navigation'
import { formatCurrency, formatDate } from '../../../../lib/utils'

import { useEffect, useState } from 'react'
import ApiClient from '../../../../lib/api'
import { useAuth } from '../../../../context/AuthContext'
import { useToast } from '../../../../context/ToastContext'
import { useTranslations } from 'next-intl'



export default function InvoiceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const invoiceId = params.invoiceId as string
  const t = useTranslations('invoiceDetail')
  const tc = useTranslations('common')

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
      setError(err.response?.data?.detail || t('loadError'))
    } finally {
      setLoading(false)
    }
  }

  const updateInvoiceStatus = async (newStatus: 'draft' | 'issued' | 'paid' | 'overdue' | 'cancelled', paidDate?: string) => {
    if (!invoice || user?.role !== 'admin') {
      showToast(t('onlyAdminCanChange'), 'error')
      return
    }

    try {
      setUpdating(true)
      await ApiClient.updateInvoiceStatus(invoice.id, {
        status: newStatus,
        paid_date: paidDate
      })

      await loadInvoice()
      showToast(t('statusUpdated', { status: newStatus === 'paid' ? t('statusPaid') : newStatus }), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('updateError'), 'error')
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
      showToast(t('submitSuccess'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('submitError'), 'error')
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
      showToast(t('approveSuccess'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('approveError'), 'error')
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!invoice || !rejectReason.trim()) {
      showToast(t('enterRejectReason'), 'error')
      return
    }
    try {
      setRejecting(true)
      await ApiClient.rejectInvoice(invoice.id, rejectReason.trim())
      setShowRejectModal(false)
      setRejectReason('')
      await loadInvoice()
      showToast(t('rejectSuccess'), 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('rejectError'), 'error')
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
    const map: Record<string, string> = {
      draft: t('statusDraft'), pending_approval: t('statusPendingApproval'),
      issued: t('statusIssued'), paid: t('statusPaidLabel'),
      overdue: t('statusOverdue'), cancelled: t('statusCancelled'),
    }
    return map[status] || status
  }

  const getPaymentTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      setup: t('paymentSetup'), monthly: t('paymentMonthly'), other: t('paymentOther'),
    }
    return map[type] || type
  }

  const handleDownloadPdf = async () => {
    if (!invoice) return

    try {
      setDownloadingPdf(true)
      const result = await ApiClient.generateInvoicePdf(invoice.id)
      if (result.pdf_url) {
        window.open(result.pdf_url, '_blank')
      }
    } catch (err: any) {
      showToast(err.response?.data?.detail || t('downloadError'), 'error')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>{t('loading')}</h1>
        </div>
      </div>
    )
  }

  if (error || !invoice) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>{t('error')}</h1>
        </div>
        <div className="card">
          <p>{error || t('notFound')}</p>
          <button className="btn-primary" onClick={() => router.back()}>
            {tc('back')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>{t('title')}</h1>
        <div className="page-header-actions">
          <button
            className="btn-primary"
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
          >
            {downloadingPdf ? t('downloading') : t('downloadPdf')}
          </button>
          <button className="btn-secondary" onClick={() => router.back()}>
            {tc('back')}
          </button>
        </div>
      </div>

      <div className="card invoice-detail-card">
        <div className="invoice-header">
          <div className="invoice-number">
            <h2>{t('invoiceNumber', { number: invoice.invoice_number })}</h2>
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
            <div className="vat-info">{t('includingVat')}</div>
          </div>
        </div>

        <div className="invoice-info">
          <div className="info-section">
            <h3>{t('invoiceInfo')}</h3>
            <div className="info-grid">
              <div className="info-item">
                <label>{t('client')}</label>
                <span>{invoice.business_name}</span>
              </div>
              <div className="info-item">
                <label>{t('invoiceNumberLabel')}</label>
                <span>{invoice.invoice_number}</span>
              </div>
              <div className="info-item">
                <label>{t('paymentType')}</label>
                <span>{getPaymentTypeLabel(invoice.payment_type)}</span>
              </div>
              <div className="info-item">
                <label>{t('currency')}</label>
                <span>{invoice.currency}</span>
              </div>
              <div className="info-item">
                <label>{t('issueDate')}</label>
                <span>{formatDate(invoice.issue_date)}</span>
              </div>
              <div className="info-item">
                <label>{t('dueDate')}</label>
                <span>{formatDate(invoice.due_date)}</span>
              </div>
              {invoice.paid_date && (
                <div className="info-item">
                  <label>{t('paidDate')}</label>
                  <span>{formatDate(invoice.paid_date)}</span>
                </div>
              )}
              {invoice.variable_symbol && (
                <div className="info-item">
                  <label>{t('variableSymbol')}</label>
                  <span>{invoice.variable_symbol}</span>
                </div>
              )}
            </div>
          </div>

          <div className="info-section">
            <h3>{t('financialDetails')}</h3>
            <div className="price-breakdown">
              <div className="price-row">
                <span>{t('amountWithoutVat')}</span>
                <span>{formatCurrency(invoice.amount_without_vat)}</span>
              </div>
              {invoice.vat_amount && (
                <div className="price-row">
                  <span>{t('vat', { rate: invoice.vat_rate })}</span>
                  <span>{formatCurrency(invoice.vat_amount)}</span>
                </div>
              )}
              <div className="price-row total">
                <span>{t('total')}</span>
                <span>{formatCurrency(invoice.amount_total)}</span>
              </div>
            </div>
          </div>
        </div>

        {invoice.description && (
          <div className="info-section">
            <h3>{t('descriptionTitle')}</h3>
            <p>{invoice.description}</p>
          </div>
        )}

        {/* Show rejection reason if invoice was rejected */}
        {invoice.rejected_reason && (
          <div className="info-section rejection-section">
            <h3>{t('rejectionReason')}</h3>
            <p className="rejection-reason">{invoice.rejected_reason}</p>
          </div>
        )}

        {/* Actions for Sales - Submit for approval */}
        {invoice.status === 'draft' && (
          <div className="invoice-actions">
            <h3>{t('actionsTitle')}</h3>
            <div className="action-buttons">
              <button
                className="btn-primary"
                onClick={handleSubmitForApproval}
                disabled={submitting}
              >
                {submitting ? t('submitting') : t('submitForApproval')}
              </button>
            </div>
            {invoice.rejected_reason && (
              <p className="action-hint">
                {t('returnedForEdit')}
              </p>
            )}
          </div>
        )}

        {/* Status info for pending approval (sales view) */}
        {invoice.status === 'pending_approval' && user?.role !== 'admin' && (
          <div className="invoice-actions">
            <h3>{t('statusTitle')}</h3>
            <p className="pending-info">
              {t('pendingApproval')}
            </p>
          </div>
        )}

        {/* Admin actions */}
        {user?.role === 'admin' && (
          <div className="invoice-actions">
            <h3>{t('adminActions')}</h3>
            <div className="action-buttons">
              {invoice.status === 'pending_approval' && (
                <>
                  <button
                    className="btn-success"
                    onClick={handleApprove}
                    disabled={approving}
                  >
                    {approving ? t('approving') : t('approveButton')}
                  </button>
                  <button
                    className="btn-danger"
                    onClick={() => setShowRejectModal(true)}
                  >
                    {t('rejectButton')}
                  </button>
                </>
              )}
              {invoice.status === 'draft' && (
                <button
                  className="btn-primary"
                  onClick={() => updateInvoiceStatus('issued')}
                  disabled={updating}
                >
                  {updating ? t('updating') : t('issueDirectly')}
                </button>
              )}
              {(invoice.status === 'issued' || invoice.status === 'overdue') && (
                <button
                  className="btn-primary"
                  onClick={() => updateInvoiceStatus('paid', new Date().toISOString().split('T')[0])}
                  disabled={updating}
                >
                  {updating ? t('updating') : t('markAsPaid')}
                </button>
              )}
              {invoice.status !== 'paid' && invoice.status !== 'cancelled' && (
                <button
                  className="btn-danger"
                  onClick={() => updateInvoiceStatus('cancelled')}
                  disabled={updating}
                >
                  {t('cancelInvoice')}
                </button>
              )}
            </div>
          </div>
        )}

        <div className="invoice-meta">
          <small>
            {t('createdAt', { date: formatDate(invoice.created_at) })}
            {invoice.updated_at && ` \u2022 ${t('updatedAt', { date: formatDate(invoice.updated_at) })}`}
          </small>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{t('rejectModal')}</h2>
            <p>{t('rejectInvoiceNumber', { number: invoice.invoice_number })}</p>
            <div className="field">
              <label htmlFor="rejectReason">{t('rejectReasonLabel')}</label>
              <textarea
                id="rejectReason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder={t('rejectReasonPlaceholder')}
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
                {tc('cancel')}
              </button>
              <button
                onClick={handleReject}
                className="btn-danger"
                disabled={rejecting || !rejectReason.trim()}
              >
                {rejecting ? t('rejecting') : t('rejectButton')}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
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
