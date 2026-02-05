'use client'

import React, { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import BusinessDetailHeader from './components/BusinessDetailHeader'
import api from '@/lib/api'

interface Business {
  id: string
  name: string
  status_crm: string
  // ... další fieldy
}

export default function BusinessDetailPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const businessId = Array.isArray(params.id) ? params.id[0] : params.id
  const [business, setBusiness] = useState<Business | null>(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!isAuthenticated || !businessId) return

    const fetchBusiness = async () => {
      try {
        const response = await api.getBusiness(businessId)
        setBusiness(response)
      } catch (error) {
        console.error('Failed to fetch business:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBusiness()
  }, [isAuthenticated, businessId])

  const handleDelete = async () => {
    if (!confirm('Opravdu chcete smazat tento lead?')) return
    
    setDeleting(true)
    try {
      await api.deleteBusiness(businessId)
      router.push('/dashboard/crm')
    } catch (error) {
      console.error('Failed to delete business:', error)
      alert('Nepodařilo se smazat lead')
    } finally {
      setDeleting(false)
    }
  }

  const handleActivityClick = () => {
    // TODO: Otevřít modal pro přidání aktivity
    console.log('Add activity clicked')
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
      <BusinessDetailHeader 
        business={business}
        onActivityClick={handleActivityClick}
        onDelete={handleDelete}
        deleting={deleting}
      />
      
      <div className="detail-content">
        {/* TODO: Zbytek komponent */}
        <p>Detail bude dokončen později...</p>
      </div>

      <style jsx>{`
        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 50vh;
          font-size: 18px;
        }

        .error-page {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 50vh;
          gap: 1rem;
        }

        .detail-page {
          padding: 1rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e5e7eb;
        }

        .header-left {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
        }

        .btn-back {
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          padding: 0.5rem 1rem;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-back:hover {
          background: #e5e7eb;
        }

        .business-title h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          color: #111827;
        }

        .test-badge {
          background: #fef3c7;
          color: #92400e;
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 500;
        }

        .status-badge {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-activity {
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 0.375rem;
          padding: 0.5rem 1rem;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-activity:hover {
          background: #2563eb;
        }

        .btn-delete {
          background: #ef4444;
          color: white;
          border: none;
          border-radius: 0.375rem;
          padding: 0.5rem 1rem;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-delete:hover:not(:disabled) {
          background: #dc2626;
        }

        .btn-delete:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .detail-content {
          margin-top: 2rem;
        }
      `}</style>
    </div>
  )
}