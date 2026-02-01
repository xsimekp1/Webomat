'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import ApiClient from '../../../lib/api'
import { useAuth } from '../../../context/AuthContext'
import { useToast } from '../../../context/ToastContext'
import { formatCurrency, formatDate } from '../../../lib/utils'

export default function InvoiceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const invoiceId = params.invoiceId as string

  const [invoice, setInvoice] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return '#666'
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
      const pdfUrl = ApiClient.downloadInvoicePdf(invoice.id)
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

        {user?.role === 'admin' && (
          <div className="invoice-actions">
            <h3>Akce</h3>
            <div className="action-buttons">
              {invoice.status === 'draft' && (
                <button
                  className="btn-primary"
                  onClick={() => updateInvoiceStatus('issued')}
                  disabled={updating}
                >
                  {updating ? 'Aktualizuji...' : 'Vystavit'}
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