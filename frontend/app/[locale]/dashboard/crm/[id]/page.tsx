'use client'

import React, { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'

export default function BusinessDetailPage() {
  const router = useRouter()
  const params = useParams()
  const businessId = Array.isArray(params.id) ? params.id[0] : params.id
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(false)
  }, [])

  if (loading) {
    return <div className="loading">Načítám detail...</div>
  }

  return (
    <div className="detail-page">
      <header className="detail-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => router.push('/dashboard/crm')}>
            ← Zpět
          </button>
          <div className="business-title">
            <h1>CRM Detail</h1>
          </div>
        </div>
      </header>

      <div className="detail-content">
        <p>Detail stránka byla zjednodušena pro rychlý deployment.</p>
      </div>

      <style jsx>{`
        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 50vh;
          font-size: 18px;
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

        .detail-content {
          margin-top: 2rem;
        }
      `}</style>
    </div>
  )
}