'use client';

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../context/AuthContext'
import { LanguageProvider, useLanguage } from '../../../context/LanguageContext'
import { supabase } from '../../../utils/supabase'
import ApiClient from '../../../lib/api'
import LanguageSwitcher from '../../../../components/LanguageSwitcher'
import { useTranslations } from 'next-intl'

interface ProfileData {
  first_name: string
  last_name: string
  email: string
  phone: string
  bank_account: string
  avatar_url: string | null
  preferred_language: string
}

function ProfileContent() {
  const t = useTranslations('profile')
  const ct = useTranslations('common')
  const { language, setLanguage } = useLanguage()
  const { user, isLoading: authLoading, isAuthenticated, refreshUser } = useAuth()
  const [profile, setProfile] = useState<ProfileData>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    bank_account: '',
    avatar_url: null,
    preferred_language: 'cs'
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [showPasswordChange, setShowPasswordChange] = useState(false)
  const [passwordData, setPasswordData] = useState({ current: '', new: '', confirm: '' })
  const [changingPassword, setChangingPassword] = useState(false)
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (user) {
      loadProfile(user.id)
    }
  }, [user])

  // Update profile when language changes in LanguageContext
  useEffect(() => {
    if (profile.preferred_language !== language) {
      setProfile(prev => ({ ...prev, preferred_language: language }))
    }
  }, [language, profile.preferred_language])

const loadProfile = async (userId: string) => {
    try {
      // Load profile through backend API (includes language preference)
      console.log('Profile: Loading profile for user:', userId);
      const userProfile = await ApiClient.getUserProfile()
      console.log('Profile: User profile loaded:', userProfile);
      
      const profileData = {
        first_name: userProfile.first_name || '',
        last_name: userProfile.last_name || '',
        email: userProfile.email || '',
        phone: userProfile.phone || '',
        bank_account: userProfile.bank_account || '',
        avatar_url: userProfile.avatar_url || null,
        preferred_language: userProfile.preferred_language || 'cs'
      };
      console.log('Profile: Setting profile data:', profileData);
      setProfile(profileData)
    } catch (err) {
      console.error('Error loading profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setProfile(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    setSaving(true)
    setMessage(null)

    try {
      const updateData = {
        first_name: profile.first_name,
        last_name: profile.last_name,
        email: profile.email,
        phone: profile.phone,
        bank_account: profile.bank_account,
        preferred_language: profile.preferred_language
      };
      console.log('Profile: Submitting update:', updateData);
      await ApiClient.updateUserProfile(updateData)
      console.log('Profile: Update successful');

      await refreshUser()

      setMessage({ type: 'success', text: t('profileSaved') })
    } catch (err: any) {
      console.error('Error saving profile:', err)
      setMessage({ type: 'error', text: err.message || t('messages.profileUpdateFailed') })
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)

    if (passwordData.new !== passwordData.confirm) {
      setMessage({ type: 'error', text: t('passwordsNotMatch') })
      return
    }

    if (passwordData.new.length < 6) {
      setMessage({ type: 'error', text: t('passwordMinLength') })
      return
    }

    setChangingPassword(true)

    try {
      await ApiClient.changePassword(passwordData.current, passwordData.new)
      setMessage({ type: 'success', text: t('passwordChanged') })
      setPasswordData({ current: '', new: '', confirm: '' })
      setShowPasswordChange(false)
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || t('messages.passwordChangeFailed') })
    } finally {
      setChangingPassword(false)
    }
  }

  const handleAvatarClick = () => {
    fileInputRef.current?.click()
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      setMessage({ type: 'error', text: t('unsupportedFormat') })
      return
    }

    if (file.size > 5 * 1024 * 1024) {
      setMessage({ type: 'error', text: t('fileTooLarge') })
      return
    }

    setUploadingAvatar(true)
    setMessage(null)

    try {
      const result = await ApiClient.uploadAvatar(file)
      setProfile(prev => ({ ...prev, avatar_url: result.avatar_url }))
      await refreshUser()
      setMessage({ type: 'success', text: t('avatarUploaded') })
    } catch (err: any) {
      console.error('Error uploading avatar:', err)
      setMessage({ type: 'error', text: err.response?.data?.detail || t('messages.avatarUploadFailed') })
    } finally {
      setUploadingAvatar(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleAvatarDelete = async () => {
    if (!confirm(t('confirmDeleteAvatar'))) return

    setUploadingAvatar(true)
    setMessage(null)

    try {
      await ApiClient.deleteAvatar()
      setProfile(prev => ({ ...prev, avatar_url: null }))
      await refreshUser()
      setMessage({ type: 'success', text: t('avatarDeleted') })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || t('messages.avatarDeleteFailed') })
    } finally {
      setUploadingAvatar(false)
    }
  }

  if (authLoading || !user || loading) {
    return <div className="loading">{ct('loading')}</div>
  }

  return (
    <>
      <main className="dashboard-main">
        <div className="profile-container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h1 style={{ margin: 0 }}>{t('title')}</h1>
            <button onClick={() => router.push('/dashboard')} className="btn-back">
              {ct('back')}
            </button>
          </div>
          <p className="profile-subtitle">{t('subtitle')}</p>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="first_name">{t('firstName')}</label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={profile.first_name}
                  onChange={handleChange}
                  placeholder={t('firstName')}
                />
              </div>

              <div className="form-group">
                <label htmlFor="last_name">{t('lastName')}</label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={profile.last_name}
                  onChange={handleChange}
                  placeholder={t('lastName')}
                />
              </div>
            </div>

            <div className="form-row">


              <div className="form-group language-field">
                <LanguageSwitcher />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">{t('email')}</label>
              <input
                type="email"
                id="email"
                name="email"
                value={profile.email}
                onChange={handleChange}
                placeholder="vas@email.cz"
              />
            </div>

            <div className="avatar-section">
              <label>{t('profilePhoto')}</label>
              <div className="avatar-container">
                <div className="avatar-preview" onClick={handleAvatarClick}>
                  {profile.avatar_url ? (
                    <img src={profile.avatar_url} alt="Avatar" />
                  ) : (
                    <div className="avatar-placeholder">
                      {profile.first_name?.[0]?.toUpperCase() || '?'}
                      {profile.last_name?.[0]?.toUpperCase() || ''}
                    </div>
                  )}
                  {uploadingAvatar && <div className="avatar-loading">...</div>}
                </div>
                <div className="avatar-actions">
                  <button type="button" onClick={handleAvatarClick} disabled={uploadingAvatar} className="btn-secondary">
                    {uploadingAvatar ? ct('loading') : t('changePhoto')}
                  </button>
                  {profile.avatar_url && (
                    <button type="button" onClick={handleAvatarDelete} disabled={uploadingAvatar} className="btn-delete-avatar">
                      {t('deletePhoto')}
                    </button>
                  )}
                </div>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                onChange={handleAvatarChange}
                style={{ display: 'none' }}
              />
              <span className="form-hint">{t('fileFormats')}</span>
            </div>

            <div className="form-group">
              <label htmlFor="phone">{t('phone')}</label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={profile.phone}
                onChange={handleChange}
                placeholder="+420 123 456 789"
              />
            </div>

            <div className="form-group">
              <label htmlFor="bank_account">{t('bankAccount')}</label>
              <input
                type="text"
                id="bank_account"
                name="bank_account"
                value={profile.bank_account}
                onChange={handleChange}
                placeholder="123456789/0100"
              />
              <span className="form-hint">{t('bankAccountHint')}</span>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-save" disabled={saving}>
                {saving ? t('saving') : t('saveChanges')}
              </button>
            </div>
          </form>

          <div className="password-section">
            <h3>{t('passwordChange')}</h3>
            {!showPasswordChange ? (
              <button
                onClick={() => setShowPasswordChange(true)}
                className="btn-secondary"
              >
                {t('changePassword')}
              </button>
            ) : (
              <form onSubmit={handlePasswordChange} className="password-form">
                <div className="form-group">
                  <label htmlFor="current_password">{t('currentPassword')}</label>
                  <input
                    type="password"
                    id="current_password"
                    value={passwordData.current}
                    onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="new_password">{t('newPassword')}</label>
                  <input
                    type="password"
                    id="new_password"
                    value={passwordData.new}
                    onChange={(e) => setPasswordData({ ...passwordData, new: e.target.value })}
                    required
                    minLength={6}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="confirm_password">{t('confirmPassword')}</label>
                  <input
                    type="password"
                    id="confirm_password"
                    value={passwordData.confirm}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })}
                    required
                  />
                </div>
                <div className="form-actions-row">
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordChange(false)
                      setPasswordData({ current: '', new: '', confirm: '' })
                    }}
                    className="btn-cancel"
                  >
                    {ct('cancel')}
                  </button>
                  <button type="submit" className="btn-save" disabled={changingPassword}>
                    {changingPassword ? ct('saving') : t('changePassword')}
                  </button>
                </div>
              </form>
            )}

            {/* Help Section */}
            <div className="help-section">
              <h3>❓ Nápověda</h3>
              <div className="help-links">
                <a href="/help" target="_blank" className="help-link">
                  📖 Jak používat Webomat
                </a>
                <a href="/help#crm" target="_blank" className="help-link">
                  🤝 CRM a obchodní procesy
                </a>
                <a href="/help#generating" target="_blank" className="help-link">
                  🎨 Tvorba webů
                </a>
                <a href="/help#billing" target="_blank" className="help-link">
                  💰 Fakturace a platby
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx>{`
        .profile-container {
          max-width: 600px;
          margin: 0 auto;
          padding: 2rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .profile-container h1 {
          margin: 0;
          color: #1a1a2e;
        }

        .profile-subtitle {
          color: #666;
          margin-bottom: 2rem;
        }

        .message {
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }

        .message.success {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }

        .message.error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }

        .profile-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-weight: 600;
          color: #333;
        }

        .form-group input {
          padding: 0.75rem 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #667eea;
        }

        .form-hint {
          font-size: 0.85rem;
          color: #888;
        }

        .avatar-section {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .avatar-section label {
          font-weight: 600;
          color: #333;
        }

        .avatar-container {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .avatar-preview {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          overflow: hidden;
          cursor: pointer;
          position: relative;
          border: 3px solid #e0e0e0;
          transition: border-color 0.2s;
        }

        .avatar-preview:hover {
          border-color: #667eea;
        }

        .avatar-preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .avatar-placeholder {
          width: 100%;
          height: 100%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .avatar-loading {
          position: absolute;
          inset: 0;
          background: rgba(0,0,0,0.5);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .avatar-actions {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .btn-delete-avatar {
          padding: 0.5rem 1rem;
          background: #f8d7da;
          color: #721c24;
          border: none;
          border-radius: 6px;
          font-size: 0.85rem;
          cursor: pointer;
        }

        .btn-delete-avatar:hover:not(:disabled) {
          background: #f5c6cb;
        }

        .btn-delete-avatar:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .form-actions {
          margin-top: 1rem;
        }

        .btn-save {
          width: 100%;
          padding: 1rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-save:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-save:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .btn-back {
          padding: 0.5rem 1rem;
          background: #f0f0f0;
          color: #333;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.9rem;
        }

        .btn-back:hover {
          background: #e0e0e0;
        }

        .password-section {
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid #e0e0e0;
        }

        .password-section h3 {
          margin: 0 0 1rem 0;
          color: #1a1a2e;
        }

        .btn-secondary {
          padding: 0.75rem 1.5rem;
          background: #f0f0f0;
          color: #333;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          cursor: pointer;
        }

        .btn-secondary:hover {
          background: #e0e0e0;
        }

        .password-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .form-actions-row {
          display: flex;
          gap: 1rem;
          margin-top: 0.5rem;
        }

        .form-actions-row .btn-save {
          flex: 1;
        }

        .btn-cancel {
          padding: 1rem;
          background: #f0f0f0;
          color: #333;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          cursor: pointer;
        }

        .btn-cancel:hover {
          background: #e0e0e0;
        }

        .language-field {
          display: flex;
          align-items: center;
          justify-content: flex-end;
        }

        .help-section {
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid #e0e0e0;
        }

        .help-section h3 {
          margin: 0 0 1rem 0;
          color: #1a1a2e;
        }

        .help-links {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.75rem;
        }

        .help-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          text-decoration: none;
          color: #374151;
          font-size: 0.9rem;
          transition: all 0.2s;
        }

        .help-link:hover {
          background: #e2e8f0;
          border-color: #cbd5e1;
          transform: translateY(-1px);
        }

        @media (max-width: 600px) {
          .profile-container > div:first-child {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
          }

          .btn-back {
            width: 100%;
          }
          .form-row {
            grid-template-columns: 1fr;
          }

          .help-links {
            grid-template-columns: 1fr;
          }

          .profile-container {
            margin: 0.5rem;
            padding: 1rem;
          }
        }
      `}</style>
    </>
  )
}

export default function ProfilePage() {
  return (
    <LanguageProvider>
      <ProfileContent />
    </LanguageProvider>
  )
}