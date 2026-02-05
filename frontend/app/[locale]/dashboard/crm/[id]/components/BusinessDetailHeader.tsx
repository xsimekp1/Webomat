import React from 'react'
import { useRouter } from 'next/navigation'

interface BusinessDetailHeaderProps {
  business: any
  onActivityClick: () => void
  onDelete: () => void
  deleting: boolean
}

export default function BusinessDetailHeader({ business, onActivityClick, onDelete, deleting }: BusinessDetailHeaderProps) {
  const router = useRouter()

  const STATUS_CONFIG = {
    new: { label: 'Nový', color: '#666', bg: '#f0f0f0' },
    calling: { label: 'Voláno', color: '#666', bg: '#f0f0f0' },
    interested: { label: 'Zájem', color: '#666', bg: '#f0f0f0' },
    offer_sent: { label: 'Nabídka', color: '#666', bg: '#f0f0f0' },
    won: { label: 'Vyhráno', color: '#22c55e', bg: '#f0fef4' },
    lost: { label: 'Ztraceno', color: '#ef4444', bg: '#fef2f2' },
    dnc: { label: 'Nekontaktovat', color: '#666', bg: '#f0f0f0' }
  }

  const isTestContact = business?.name?.toLowerCase().includes('test') ||
                       business?.name?.toLowerCase().includes('demo') ||
                       business?.name?.toLowerCase().includes('sample')

  return (
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
          >
            {STATUS_CONFIG[business.status_crm]?.label || business.status_crm}
          </span>
        </div>
      </div>
      <div className="header-actions">
        <button className="btn-activity" onClick={onActivityClick}>
          + Přidat aktivitu
        </button>
        <button className="btn-delete" onClick={onDelete} disabled={deleting}>
          {deleting ? 'Mažu...' : 'Smazat'}
        </button>
      </div>
    </header>
  )
}