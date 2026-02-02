'use client'

import { useEffect, useState } from 'react'
import ApiClient from './../lib/api'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'
import { LanguageProvider } from '@/context/LanguageContext'
import { useTranslations } from 'next-intl'

interface LedgerEntry {
  id: string
  entry_type: string
  amount: number
  description?: string
  created_at: string
  related_business_id?: string
  related_project_id?: string
  business_name?: string
  project_status?: string
}

interface AccountSummary {
  total_earned: number
  total_paid_out: number
  available_balance: number
  pending_commissions: number
  reserved_for_payout: number
}

function AccountContent() {
  const { user } = useAuth()
  const { language } = useLanguage()
  const t = useTranslations('account')
  
  const [ledgerData, setLedgerData] = useState<LedgerEntry[]>([])
  const [accountSummary, setAccountSummary] = useState<AccountSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Filtry
  const [dateRange, setDateRange] = useState('3months')
  const [entryType, setEntryType] = useState('all')
  const [entryStatus, setEntryStatus] = useState('all')

  useEffect(() => {
    if (user) {
      loadAccountData()
    }
  }, [user, dateRange, entryType, entryStatus])

  const loadAccountData = async () => {
    try {
      setLoading(true)
      
      // Načti ledger data
      const ledgerResponse = await ApiClient.getSellerAccountLedger({
        range: dateRange,
        type: entryType,
        status: entryStatus
      })
      
      setLedgerData(ledgerResponse.entries || [])
      setAccountSummary(ledgerResponse.summary)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodařilo se načíst data účtu')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat(language === 'en' ? 'en-US' : 'cs-CZ', {
      style: 'currency',
      currency: 'CZK',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString(language === 'en' ? 'en-US' : 'cs-CZ')
  }

  const getEntryTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      commission_earned: t('commissionEarned'),
      admin_adjustment: t('adminAdjustment'),
      payout_reserved: t('payoutReserved'),
      payout_paid: t('payoutPaid')
    }
    return labels[type] || type
  }

  const getEntryTypeClass = (type: string) => {
    const classes: Record<string, string> = {
      commission_earned: 'positive',
      admin_adjustment: 'adjustment',
      payout_reserved: 'reserved',
      payout_paid: 'payout'
    }
    return classes[type] || 'default'
  }

  const formatDescription = (entry: LedgerEntry) => {
    if (entry.description) return entry.description
    
    // Automaticky generuj popis pro různé typy
    switch (entry.entry_type) {
      case 'commission_earned':
        return entry.business_name 
          ? (language === 'en' ? `Commission from ${entry.business_name}` : `Provize z ${entry.business_name}`)
          : t('commissionEarned')
      case 'payout_paid':
        return t('payoutPaid')
      case 'payout_reserved':
        return t('reservedForPayout')
      case 'admin_adjustment':
        return t('adminAdjustment')
      default:
        return ''
    }
  }

  if (!user) {
    return <div className="loading">Načítám...</div>
  }

  if (loading && !accountSummary) {
    return <div className="loading">{t('loading')}</div>
  }

  return (
    <div className="account-page">
      <div className="page-header">
        <h1>{t('title')}</h1>
        <div className="language-switcher-wrapper">
          <div className="current-lang-flag">
            {language === 'en' ? '🇬🇧' : '🇨🇿'}
          </div>
          <span className="current-lang-text">
            {language === 'en' ? 'English' : 'Česky'}
          </span>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Account Summary Cards */}
      {accountSummary && (
        <div className="summary-grid">
          <div className="summary-card available">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <span className="card-value">{formatCurrency(accountSummary.available_balance)}</span>
              <span className="card-label">{t('availableToPayout')}</span>
            </div>
          </div>

          <div className="summary-card earned">
            <div className="card-icon">📈</div>
            <div className="card-content">
              <span className="card-value">{formatCurrency(accountSummary.total_earned)}</span>
              <span className="card-label">{t('totalEarned')}</span>
            </div>
          </div>

          <div className="summary-card paid">
            <div className="card-icon">✅</div>
            <div className="card-content">
              <span className="card-value">{formatCurrency(accountSummary.total_paid_out)}</span>
              <span className="card-label">{t('alreadyPaidOut')}</span>
            </div>
          </div>

          <div className="summary-card pending">
            <div className="card-icon">⏳</div>
            <div className="card-content">
              <span className="card-value">{formatCurrency(accountSummary.pending_commissions)}</span>
              <span className="card-label">{t('pendingCommissions')}</span>
            </div>
          </div>
        </div>
      )}

      {/* Account Balance Breakdown */}
      {accountSummary && (
        <div className="balance-breakdown">
          <h2>{t('balanceCalculation')}</h2>
          <div className="breakdown-formula">
            <div className="formula-row positive">
              <span className="formula-label">{t('totalCommissionsEarned')}:</span>
              <span className="formula-value">+{formatCurrency(accountSummary.total_earned)}</span>
            </div>
            
            <div className="formula-row negative">
              <span className="formula-label">{t('adminAdjustments')}:</span>
              <span className="formula-value">
                {formatCurrency(accountSummary.total_paid_out - accountSummary.total_earned + accountSummary.available_balance + accountSummary.pending_commissions)}
              </span>
            </div>
            
            <div className="formula-row negative">
              <span className="formula-label">{t('paidOut')}:</span>
              <span className="formula-value">-{formatCurrency(accountSummary.total_paid_out)}</span>
            </div>
            
            <div className="divider"></div>
            
            <div className="formula-row result">
              <span className="formula-label">{t('availableBalance')}:</span>
              <span className="formula-value">{formatCurrency(accountSummary.available_balance)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <h3>{t('transactionHistory')}</h3>
        <div className="filters">
          <div className="filter-group">
            <label>{t('timeRange')}:</label>
            <select value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
              <option value="1month">{t('lastMonth')}</option>
              <option value="3months">{t('last3Months')}</option>
              <option value="6months">{t('last6Months')}</option>
              <option value="1year">{t('lastYear')}</option>
              <option value="all">{t('allTime')}</option>
            </select>
          </div>

          <div className="filter-group">
            <label>{t('type')}:</label>
            <select value={entryType} onChange={(e) => setEntryType(e.target.value)}>
              <option value="all">{t('allTypes')}</option>
              <option value="commission_earned">{t('commissions')}</option>
              <option value="admin_adjustment">{t('adjustments')}</option>
              <option value="payout_reserved">{t('reservedForPayout')}</option>
              <option value="payout_paid">{t('paidOutShort')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Ledger Entries Table */}
      <div className="ledger-section">
        {loading ? (
          <div className="loading">{language === 'en' ? 'Loading...' : 'Načítám...'}</div>
        ) : ledgerData.length === 0 ? (
          <div className="empty-state">
            <p>{t('noTransactionsFound')}</p>
          </div>
        ) : (
          <div className="ledger-table">
            <div className="table-header">
              <div className="col-date">{t('date')}</div>
              <div className="col-type">{t('type')}</div>
              <div className="col-description">{t('description')}</div>
              <div className="col-amount">{t('amount')}</div>
            </div>
            
            {ledgerData.map((entry) => (
              <div key={entry.id} className={`table-row ${getEntryTypeClass(entry.entry_type)}`}>
                <div className="col-date">{formatDate(entry.created_at)}</div>
                <div className="col-type">
                  <span className="entry-type-badge">{getEntryTypeLabel(entry.entry_type)}</span>
                </div>
                <div className="col-description">{formatDescription(entry)}</div>
                <div className={`col-amount ${entry.amount > 0 ? 'positive' : 'negative'}`}>
                  {entry.amount > 0 ? '+' : ''}{formatCurrency(entry.amount)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .account-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }

        .page-header h1 {
          font-size: 2rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0;
        }

        .language-switcher-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
        }

        .current-lang-flag {
          font-size: 1.2rem;
        }

        .current-lang-text {
          font-size: 0.9rem;
          font-weight: 500;
          color: #374151;
        }

        .loading {
          text-align: center;
          padding: 48px;
          color: #64748b;
          font-size: 1.1rem;
        }

        .error-message {
          background: #fef2f2;
          color: #dc2626;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 24px;
          border: 1px solid #fecaca;
        }

        /* Summary Grid */
        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 32px;
        }

        .summary-card {
          background: white;
          border-radius: 16px;
          padding: 24px;
          border: 1px solid #e2e8f0;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .summary-card.available {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .summary-card.earned {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          border: none;
        }

        .summary-card.paid {
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          color: white;
          border: none;
        }

        .summary-card.pending {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          color: white;
          border: none;
        }

        .card-icon {
          font-size: 2.5rem;
          opacity: 0.9;
        }

        .card-content {
          flex: 1;
        }

        .card-value {
          display: block;
          font-size: 1.75rem;
          font-weight: 700;
          line-height: 1.2;
        }

        .card-label {
          display: block;
          font-size: 0.9rem;
          opacity: 0.9;
          margin-top: 4px;
        }

        /* Balance Breakdown */
        .balance-breakdown {
          background: white;
          border-radius: 16px;
          padding: 24px;
          margin-bottom: 32px;
          border: 1px solid #e2e8f0;
        }

        .balance-breakdown h2 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1e293b;
          margin: 0 0 24px 0;
        }

        .breakdown-formula {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .formula-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-radius: 8px;
          font-weight: 500;
        }

        .formula-row.positive {
          background: #dcfce7;
          color: #166534;
        }

        .formula-row.negative {
          background: #fef2f2;
          color: #dc2626;
        }

        .formula-row.result {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          font-size: 1.1rem;
          font-weight: 700;
        }

        .formula-label {
          flex: 1;
        }

        .formula-value {
          font-weight: 700;
          font-family: 'Courier New', monospace;
        }

        .divider {
          height: 1px;
          background: #e5e7eb;
          margin: 8px 0;
        }

        /* Filters */
        .filters-section {
          background: white;
          border-radius: 16px;
          padding: 24px;
          margin-bottom: 24px;
          border: 1px solid #e2e8f0;
        }

        .filters-section h3 {
          font-size: 1.25rem;
          font-weight: 600;
          color: #1e293b;
          margin: 0 0 20px 0;
        }

        .filters {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .filter-group label {
          font-size: 0.9rem;
          font-weight: 500;
          color: #374151;
        }

        .filter-group select {
          padding: 10px 14px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 0.95rem;
          background: white;
          cursor: pointer;
        }

        .filter-group select:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        /* Ledger Table */
        .ledger-section {
          background: white;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          overflow: hidden;
        }

        .ledger-table {
          width: 100%;
        }

        .table-header {
          display: grid;
          grid-template-columns: 120px 180px 1fr 140px;
          gap: 16px;
          padding: 16px 24px;
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
          font-weight: 600;
          color: #374151;
          font-size: 0.9rem;
        }

        .table-row {
          display: grid;
          grid-template-columns: 120px 180px 1fr 140px;
          gap: 16px;
          padding: 16px 24px;
          border-bottom: 1px solid #f1f5f9;
          transition: background-color 0.2s;
        }

        .table-row:hover {
          background: #f8fafc;
        }

        .table-row.positive {
          border-left: 3px solid #10b981;
        }

        .table-row.negative {
          border-left: 3px solid #dc2626;
        }

        .table-row.adjustment {
          border-left: 3px solid #f59e0b;
        }

        .table-row.reserved {
          border-left: 3px solid #3b82f6;
        }

        .table-row.payout {
          border-left: 3px solid #8b5cf6;
        }

        .col-date {
          font-size: 0.9rem;
          color: #64748b;
        }

        .entry-type-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
          background: #f1f5f9;
          color: #475569;
        }

        .col-description {
          color: #1e293b;
          font-size: 0.95rem;
        }

        .col-amount {
          text-align: right;
          font-weight: 600;
          font-family: 'Courier New', monospace;
        }

        .col-amount.positive {
          color: #10b981;
        }

        .col-amount.negative {
          color: #dc2626;
        }

        .empty-state {
          text-align: center;
          padding: 48px;
          color: #64748b;
        }

        @media (max-width: 768px) {
          .account-page {
            padding: 16px;
          }

          .page-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 16px;
          }

          .summary-grid {
            grid-template-columns: 1fr;
          }

          .table-header,
          .table-row {
            grid-template-columns: 1fr;
            gap: 8px;
          }

          .table-header > *:not(:first-child),
          .table-row > *:not(:first-child) {
            display: none;
          }

          .filters {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}

export default function AccountPage() {
  return (
    <LanguageProvider>
      <AccountContent />
    </LanguageProvider>
  )
}
