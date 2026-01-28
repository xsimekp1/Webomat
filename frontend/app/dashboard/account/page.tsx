'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../context/AuthContext'
import ApiClient from '../../lib/api'

type MovementType =
  | 'commission'
  | 'bonus'
  | 'payout'
  | 'adjustment'
  | 'refund'
  | 'chargeback'
  | 'other'

type MovementStatus = 'pending' | 'available' | 'paid' | 'canceled'

interface SellerAccountMovement {
  id: string
  created_at: string

  type: MovementType
  status: MovementStatus

  amount: number
  currency?: string // default CZK

  description?: string

  business_id?: string | null
  business_name?: string | null

  invoice_id?: string | null
  invoice_number?: string | null

  // pokud umíte z backendu vracet:
  balance_after?: number | null
}

interface SellerAccountLedgerResponse {
  available_balance: number
  pending_balance?: number
  movements: SellerAccountMovement[]
}

export default function AccountMovementsPage() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const router = useRouter()

  const [data, setData] = useState<SellerAccountLedgerResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // Filtry
  const [range, setRange] = useState<'30' | '90' | 'all'>('90')
  const [type, setType] = useState<'all' | MovementType>('all')
  const [status, setStatus] = useState<'all' | MovementStatus>('all')

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/')
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (!isAuthenticated) return
    setLoading(true)
    setError('')

    ApiClient.getSellerAccountLedger({ range, type, status })
      .then(setData)
      .catch((e: any) => {
        setError(e?.response?.data?.detail || 'Nepodařilo se načíst pohyby na účtu.')
      })
      .finally(() => setLoading(false))
  }, [isAuthenticated, range, type, status])

  const formatCurrency = (amount: number, currency = 'CZK') =>
    new Intl.NumberFormat('cs-CZ', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)

  const formatDateTime = (iso: string) => {
    const d = new Date(iso)
    const dd = d.getDate()
    const mm = d.getMonth() + 1
    const yyyy = d.getFullYear()
    const hh = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    return `${dd}.${mm}.${yyyy} ${hh}:${mi}`
  }

  const typeLabel = (t: MovementType) => {
    const map: Record<MovementType, string> = {
      commission: 'Provize',
      bonus: 'Bonus',
      payout: 'Výplata',
      adjustment: 'Úprava',
      refund: 'Refund',
      chargeback: 'Chargeback',
      other: 'Ostatní',
    }
    return map[t] ?? t
  }

  const statusLabel = (s: MovementStatus) => {
    const map: Record<MovementStatus, string> = {
      pending: 'Čeká',
      available: 'K vyplacení',
      paid: 'Vyplaceno',
      canceled: 'Stornováno',
    }
    return map[s] ?? s
  }

  const filteredMovements = useMemo(() => data?.movements ?? [], [data])

  const totals = useMemo(() => {
    const m = filteredMovements
    const credits = m.filter(x => x.amount > 0).reduce((sum, x) => sum + x.amount, 0)
    const debits = m.filter(x => x.amount < 0).reduce((sum, x) => sum + x.amount, 0)
    return { credits, debits }
  }, [filteredMovements])

  if (isLoading || !user) return <div className="loading">Načítám...</div>

  return (
    <div className="page">
      <header className="header">
        <div className="header-left" onClick={() => router.push('/dashboard')} role="button" tabIndex={0}>
          <h1>Webomat</h1>
          <span className="breadcrumb">/ Pohyby na účtu</span>
        </div>

        <div className="header-right">
          <span className="user-info">
            {user.name}{' '}
            <span className="role-badge">{user.role === 'admin' ? 'Admin' : 'Obchodník'}</span>
          </span>
          <button onClick={() => router.push('/help')} className="btn-icon" title="Nápověda">
            ?
          </button>
          <button onClick={() => router.push('/dashboard/profile')} className="btn-icon" title="Můj profil">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>
          <button onClick={logout} className="btn-logout">
            Odhlásit
          </button>
        </div>
      </header>

      <main className="main">
        <div className="top">
          <div className="cards">
            <div className="stat-card primary">
              <div className="stat-title">K vyplacení</div>
              <div className="stat-value">
                {formatCurrency(data?.available_balance ?? 0, 'CZK')}
              </div>
              <div className="stat-sub">Zůstatek dostupný pro výplatu</div>
            </div>

            <div className="stat-card">
              <div className="stat-title">Součet příjmů (filtr)</div>
              <div className="stat-value">{formatCurrency(totals.credits, 'CZK')}</div>
              <div className="stat-sub">Jen položky v tabulce</div>
            </div>

            <div className="stat-card">
              <div className="stat-title">Součet odpisů (filtr)</div>
              <div className="stat-value">{formatCurrency(totals.debits, 'CZK')}</div>
              <div className="stat-sub">Záporné položky v tabulce</div>
            </div>
          </div>

          <div className="filters">
            <div className="filter">
              <label>Období</label>
              <select value={range} onChange={(e) => setRange(e.target.value as any)}>
                <option value="30">Posledních 30 dní</option>
                <option value="90">Posledních 90 dní</option>
                <option value="all">Vše</option>
              </select>
            </div>

            <div className="filter">
              <label>Typ</label>
              <select value={type} onChange={(e) => setType(e.target.value as any)}>
                <option value="all">Vše</option>
                <option value="commission">Provize</option>
                <option value="bonus">Bonus</option>
                <option value="payout">Výplata</option>
                <option value="adjustment">Úprava</option>
                <option value="refund">Refund</option>
                <option value="chargeback">Chargeback</option>
                <option value="other">Ostatní</option>
              </select>
            </div>

            <div className="filter">
              <label>Stav</label>
              <select value={status} onChange={(e) => setStatus(e.target.value as any)}>
                <option value="all">Vše</option>
                <option value="pending">Čeká</option>
                <option value="available">K vyplacení</option>
                <option value="paid">Vyplaceno</option>
                <option value="canceled">Stornováno</option>
              </select>
            </div>

            <button className="btn-back" onClick={() => router.push('/dashboard')}>
              ← Zpět na dashboard
            </button>
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        <section className="table-card">
          <div className="table-head">
            <h2>Pohyby</h2>
            <span className="count">
              {loading ? 'Načítám…' : `${filteredMovements.length} položek`}
            </span>
          </div>

          {loading ? (
            <div className="loading-row">Načítám pohyby na účtu…</div>
          ) : filteredMovements.length === 0 ? (
            <div className="empty">
              <p>Žádné pohyby pro zvolené filtry.</p>
              <small>Zkus změnit období/typ/stav.</small>
            </div>
          ) : (
            <div className="table">
              <div className="row head">
                <div>Datum</div>
                <div>Typ</div>
                <div>Klient</div>
                <div>Doklad</div>
                <div>Popis</div>
                <div className="right">Částka</div>
                <div>Stav</div>
                <div className="right">Zůstatek</div>
              </div>

              {filteredMovements.map((m) => (
                <div
                  key={m.id}
                  className="row"
                  onClick={() => m.business_id ? router.push(`/dashboard/crm/${m.business_id}`) : undefined}
                  style={{ cursor: m.business_id ? 'pointer' : 'default' }}
                  title={m.business_id ? 'Otevřít klienta v CRM' : ''}
                >
                  <div className="mono">{formatDateTime(m.created_at)}</div>
                  <div>
                    <span className={`badge type-${m.type}`}>{typeLabel(m.type)}</span>
                  </div>
                  <div className="truncate">{m.business_name || '—'}</div>
                  <div className="mono">{m.invoice_number || '—'}</div>
                  <div className="truncate">{m.description || '—'}</div>
                  <div className={`right amount ${m.amount >= 0 ? 'pos' : 'neg'}`}>
                    {formatCurrency(m.amount, m.currency || 'CZK')}
                  </div>
                  <div>
                    <span className={`badge status-${m.status}`}>{statusLabel(m.status)}</span>
                  </div>
                  <div className="right mono">
                    {m.balance_after != null ? formatCurrency(m.balance_after, m.currency || 'CZK') : '—'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      <style jsx>{`
        .page {
          min-height: 100vh;
          background: #f8fafc;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          background: white;
          border-bottom: 1px solid #e2e8f0;
          position: sticky;
          top: 0;
          z-index: 100;
        }

        .header-left {
          display: flex;
          align-items: baseline;
          gap: 10px;
          cursor: pointer;
        }

        .header-left h1 {
          font-size: 1.5rem;
          font-weight: 700;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
        }

        .breadcrumb {
          color: #94a3b8;
          font-size: 0.9rem;
          font-weight: 500;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .user-info {
          font-size: 0.9rem;
          color: #64748b;
        }

        .role-badge {
          background: #f1f5f9;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.75rem;
          margin-left: 4px;
        }

        .btn-icon {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border: 1px solid #e2e8f0;
          background: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }

        .btn-icon:hover {
          background: #f8fafc;
          border-color: #cbd5e1;
        }

        .btn-logout {
          padding: 8px 16px;
          background: #fee2e2;
          color: #dc2626;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-logout:hover {
          background: #fecaca;
        }

        .main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        .top {
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 16px;
          margin-bottom: 16px;
          align-items: start;
        }

        .cards {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
        }

        .stat-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 16px;
        }

        .stat-card.primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .stat-title {
          font-size: 0.85rem;
          opacity: 0.9;
          font-weight: 600;
        }

        .stat-value {
          font-size: 1.8rem;
          font-weight: 800;
          margin-top: 6px;
        }

        .stat-sub {
          margin-top: 6px;
          font-size: 0.85rem;
          opacity: 0.85;
        }

        .filters {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .filter label {
          display: block;
          font-size: 0.8rem;
          font-weight: 600;
          color: #475569;
          margin-bottom: 6px;
        }

        .filter select {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid #d1d5db;
          border-radius: 10px;
          background: white;
          font-size: 0.95rem;
        }

        .btn-back {
          padding: 10px 12px;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
          background: #f8fafc;
          cursor: pointer;
          font-weight: 600;
        }

        .btn-back:hover {
          background: #f1f5f9;
        }

        .error {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 12px 14px;
          border-radius: 12px;
          margin-bottom: 16px;
        }

        .table-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          overflow: hidden;
        }

        .table-head {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          padding: 16px 16px 10px 16px;
          border-bottom: 1px solid #e2e8f0;
        }

        .table-head h2 {
          margin: 0;
          font-size: 1.1rem;
          color: #0f172a;
        }

        .count {
          color: #64748b;
          font-size: 0.9rem;
        }

        .loading-row {
          padding: 18px 16px;
          color: #64748b;
        }

        .empty {
          padding: 32px 16px;
          text-align: center;
          color: #64748b;
        }

        .table {
          width: 100%;
          overflow-x: auto;
        }

        .row {
          display: grid;
          grid-template-columns: 140px 120px 180px 110px 1fr 130px 120px 140px;
          gap: 12px;
          padding: 12px 16px;
          border-bottom: 1px solid #f1f5f9;
          align-items: center;
          min-width: 1100px;
        }

        .row.head {
          background: #f8fafc;
          font-weight: 700;
          color: #475569;
          font-size: 0.85rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .truncate {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .right {
          text-align: right;
        }

        .mono {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        .amount.pos { color: #059669; font-weight: 700; }
        .amount.neg { color: #dc2626; font-weight: 700; }

        .badge {
          display: inline-flex;
          align-items: center;
          padding: 3px 10px;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 700;
          border: 1px solid transparent;
        }

        .type-commission { background: #ecfeff; color: #155e75; border-color: #a5f3fc; }
        .type-bonus { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }
        .type-payout { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
        .type-adjustment { background: #f1f5f9; color: #334155; border-color: #e2e8f0; }
        .type-refund, .type-chargeback { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
        .type-other { background: #f8fafc; color: #475569; border-color: #e2e8f0; }

        .status-pending { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
        .status-available { background: #ecfeff; color: #155e75; border-color: #a5f3fc; }
        .status-paid { background: #ecfdf5; color: #065f46; border-color: #a7f3d0; }
        .status-canceled { background: #fef2f2; color: #991b1b; border-color: #fecaca; }

        @media (max-width: 980px) {
          .top { grid-template-columns: 1fr; }
          .cards { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  )
}
