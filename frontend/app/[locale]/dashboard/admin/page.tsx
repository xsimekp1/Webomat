'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import ApiClient from '../../../../lib/api'

interface UserListItem {
  id: string
  first_name: string
  last_name: string
  email: string
  role: 'admin' | 'sales'
  is_active: boolean
  created_at: string | null
}

export default function AdminUsersPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<UserListItem[]>([])
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [resetPasswordModal, setResetPasswordModal] = useState<{
    userId: string
    userName: string
  } | null>(null)
  const [newPassword, setNewPassword] = useState('')
  const [resetting, setResetting] = useState(false)

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/')
      } else if (user?.role !== 'admin') {
        router.push('/dashboard')
      }
    }
  }, [isLoading, isAuthenticated, user, router])

  useEffect(() => {
    if (user?.role === 'admin') {
      loadUsers()
    }
  }, [user])

  const loadUsers = async () => {
    try {
      setLoadingUsers(true)
      const data = await ApiClient.getUsers()
      setUsers(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodařilo se načíst uživatele')
    } finally {
      setLoadingUsers(false)
    }
  }

  const handleToggleActive = async (userId: string) => {
    try {
      const result = await ApiClient.toggleUserActive(userId)
      setSuccessMessage(result.message)
      loadUsers()
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Akce se nezdařila')
      setTimeout(() => setError(''), 3000)
    }
  }

  const handleResetPassword = async () => {
    if (!resetPasswordModal) return

    try {
      setResetting(true)
      const result = await ApiClient.resetUserPassword(
        resetPasswordModal.userId,
        newPassword || undefined
      )
      setSuccessMessage(
        `${result.message}. Dočasné heslo: ${result.temporary_password}`
      )
      setResetPasswordModal(null)
      setNewPassword('')
      setTimeout(() => setSuccessMessage(''), 10000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reset hesla selhal')
      setTimeout(() => setError(''), 3000)
    } finally {
      setResetting(false)
    }
  }

  if (isLoading || !user) {
    return <div className="loading">Načítám...</div>
  }

  if (user.role !== 'admin') {
    return null
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <button onClick={() => router.push('/dashboard')} className="btn-back">
          Zpět na dashboard
        </button>
        <h1>Správa uživatelů</h1>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {successMessage && <div className="alert alert-success">{successMessage}</div>}

      <main className="admin-main">
        {loadingUsers ? (
          <div className="loading">Načítám uživatele...</div>
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>Jméno</th>
                <th>Email</th>
                <th>Role</th>
                <th>Stav</th>
                <th>Akce</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className={!u.is_active ? 'inactive' : ''}>
                  <td>{u.first_name} {u.last_name}</td>
                  <td>{u.email}</td>
                  <td>{u.role === 'admin' ? 'Admin' : 'Obchodník'}</td>
                  <td>
                    <span className={`status-badge ${u.is_active ? 'active' : 'inactive'}`}>
                      {u.is_active ? 'Aktivní' : 'Neaktivní'}
                    </span>
                  </td>
                  <td className="actions">
                    <button
                      onClick={() => setResetPasswordModal({
                        userId: u.id,
                        userName: `${u.first_name} ${u.last_name}`
                      })}
                      className="btn-small"
                    >
                      Reset hesla
                    </button>
                    {u.id !== user.id && (
                      <button
                        onClick={() => handleToggleActive(u.id)}
                        className={`btn-small ${u.is_active ? 'btn-danger' : 'btn-success'}`}
                      >
                        {u.is_active ? 'Deaktivovat' : 'Aktivovat'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>

      {resetPasswordModal && (
        <div className="modal-overlay" onClick={() => setResetPasswordModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Reset hesla</h2>
            <p>Resetovat heslo pro: <strong>{resetPasswordModal.userName}</strong></p>
            <div className="field">
              <label htmlFor="newPassword">Nové heslo (prázdné = vygenerovat)</label>
              <input
                id="newPassword"
                type="text"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Nechat prázdné pro automatické heslo"
              />
            </div>
            <div className="modal-actions">
              <button
                onClick={() => setResetPasswordModal(null)}
                className="btn-secondary"
                disabled={resetting}
              >
                Zrušit
              </button>
              <button
                onClick={handleResetPassword}
                className="btn-primary"
                disabled={resetting}
              >
                {resetting ? 'Resetuji...' : 'Resetovat heslo'}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .admin-page {
          min-height: 100vh;
          background: #f5f5f5;
        }
        .admin-header {
          background: #1a1a2e;
          color: white;
          padding: 1rem 2rem;
          display: flex;
          align-items: center;
          gap: 2rem;
        }
        .admin-header h1 {
          margin: 0;
          font-size: 1.5rem;
        }
        .btn-back {
          background: transparent;
          border: 1px solid #fff;
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
        }
        .btn-back:hover {
          background: rgba(255,255,255,0.1);
        }
        .admin-main {
          padding: 2rem;
        }
        .alert {
          padding: 1rem;
          border-radius: 4px;
          margin: 1rem 2rem;
        }
        .alert-error {
          background: #fee;
          color: #c00;
          border: 1px solid #fcc;
        }
        .alert-success {
          background: #efe;
          color: #060;
          border: 1px solid #cfc;
        }
        .users-table {
          width: 100%;
          background: white;
          border-collapse: collapse;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .users-table th,
        .users-table td {
          padding: 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }
        .users-table th {
          background: #f8f9fa;
          font-weight: 600;
        }
        .users-table tr.inactive {
          opacity: 0.6;
        }
        .status-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.85rem;
        }
        .status-badge.active {
          background: #d4edda;
          color: #155724;
        }
        .status-badge.inactive {
          background: #f8d7da;
          color: #721c24;
        }
        .actions {
          display: flex;
          gap: 0.5rem;
        }
        .btn-small {
          padding: 0.4rem 0.8rem;
          font-size: 0.85rem;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          background: #6c757d;
          color: white;
        }
        .btn-small:hover {
          background: #5a6268;
        }
        .btn-danger {
          background: #dc3545;
        }
        .btn-danger:hover {
          background: #c82333;
        }
        .btn-success {
          background: #28a745;
        }
        .btn-success:hover {
          background: #218838;
        }
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        .modal {
          background: white;
          padding: 2rem;
          border-radius: 8px;
          max-width: 400px;
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
        .field input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
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
        .btn-primary {
          background: #007bff;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
        }
        .btn-primary:hover {
          background: #0069d9;
        }
        .btn-secondary:hover {
          background: #5a6268;
        }
        .loading {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
      `}</style>
    </div>
  )
}
