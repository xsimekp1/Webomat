'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../context/AuthContext'
import FeedbackModal from './feedback/FeedbackModal'

export default function DashboardHeader() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [showFeedback, setShowFeedback] = useState(false)

  return (
    <>
      <header className="dashboard-header">
        <div className="header-left">
          <h1 onClick={() => router.push('/dashboard')} style={{ cursor: 'pointer' }}>
            Webomat
          </h1>
        </div>
        <div className="header-right">
          {user ? (
            <>
              <span className="user-info">
                {user.name} <span className="role-badge">{user.role === 'admin' ? 'Admin' : 'Obchodník'}</span>
              </span>

              {/* Feedback button for all users */}
              <button
                onClick={() => setShowFeedback(true)}
                className="btn-feedback-text"
                title="Připomínky k platformě"
              >
                💬 Připomínky
              </button>

              {/* Admin: link to invoices management */}
              {user.role === 'admin' && (
                <button
                  onClick={() => router.push('/dashboard/admin/invoices')}
                  className="btn-nav"
                  title="Správa faktur"
                >
                  Faktury
                </button>
              )}

              {/* Admin: link to feedback management */}
              {user.role === 'admin' && (
                <button
                  onClick={() => router.push('/dashboard/admin/feedback')}
                  className="btn-icon"
                  title="Správa připomínek"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10,9 9,9 8,9"/>
                  </svg>
                </button>
              )}


              <button onClick={() => router.push('/dashboard/profile')} className="btn-icon" title="Můj profil">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </button>
              <button onClick={logout} className="btn-logout">
                Odhlásit
              </button>
            </>
          ) : (
            <span className="user-info">Načítám...</span>
          )}
        </div>
      </header>

        <style jsx>{`
          .dashboard-header {
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

          .header-left h1 {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            transition: opacity 0.2s;
          }

          .header-left h1:hover {
            opacity: 0.8;
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

          .btn-nav {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            background: white;
            color: #374151;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s;
          }

          .btn-nav:hover {
            background: #f8fafc;
            border-color: #667eea;
            color: #667eea;
          }

          .btn-feedback-text {
            padding: 8px 16px;
            border-radius: 8px;
            border: 2px solid #667eea;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s;
          }

          .btn-feedback-text:hover {
            opacity: 0.9;
            transform: scale(1.02);
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

          @media (max-width: 768px) {
            .dashboard-header {
              padding: 12px 16px;
            }

            .user-info {
              display: none;
            }
          }
        `}</style>

      <FeedbackModal isOpen={showFeedback} onClose={() => setShowFeedback(false)} />
    </>
  )
}
