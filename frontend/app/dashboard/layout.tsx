'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import DashboardHeader from '../components/DashboardHeader'
import FeedbackButton from '../components/feedback/FeedbackButton'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading">Načítám...</div>
        <style jsx>{`
          .loading-container {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: #f8fafc;
          }
          .loading {
            font-size: 1.1rem;
            color: #64748b;
          }
        `}</style>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="dashboard-layout">
      <DashboardHeader />
      <main className="dashboard-content">
        {children}
      </main>
      <FeedbackButton />

      <style jsx>{`
        .dashboard-layout {
          min-height: 100vh;
          background: #f8fafc;
        }

        .dashboard-content {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        @media (max-width: 768px) {
          .dashboard-content {
            padding: 16px;
          }
        }
      `}</style>
    </div>
  )
}
