'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { User, supabase } from '../../lib/supabase'

interface ProfileData {
  first_name: string
  last_name: string
  email: string
  phone: string
  bank_account: string
  profile_photo_url?: string
  theme: 'light' | 'dark'
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<ProfileData>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    bank_account: '',
    profile_photo_url: '',
    theme: 'light'
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const router = useRouter()

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser)
      setUser(parsedUser)
      loadProfile(parsedUser.id)
    } else {
      router.push('/')
    }
  }, [router])

  const loadProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('sellers')
        .select('first_name, last_name, email, phone, bank_account, profile_photo_url')
        .eq('id', userId)
        .single()

      if (error) throw error

      if (data) {
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' || 'light'
        setProfile({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          email: data.email || '',
          phone: data.phone || '',
          bank_account: data.bank_account || '',
          profile_photo_url: data.profile_photo_url || '',
          theme: savedTheme
        })
      }
    } catch (err) {
      console.error('Error loading profile:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setProfile(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !user) return

    try {
      const fileExt = file.name.split('.').pop()
      const fileName = `${user.id}_${Date.now()}.${fileExt}`
      const filePath = `profile-photos/${fileName}`

      const { error: uploadError } = await supabase.storage
        .from('assets')
        .upload(filePath, file)

      if (uploadError) throw uploadError

      const { data: { publicUrl } } = supabase.storage
        .from('assets')
        .getPublicUrl(filePath)

      setProfile(prev => ({ ...prev, profile_photo_url: publicUrl }))
      setMessage({ type: 'success', text: 'Fotka byla úspěšně nahrána!' })
    } catch (err: any) {
      console.error('Error uploading photo:', err)
      setMessage({ type: 'error', text: err.message || 'Nepodařilo se nahrát fotku' })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return

    setSaving(true)
    setMessage(null)

    try {
      const { error } = await supabase
        .from('sellers')
        .update({
          first_name: profile.first_name,
          last_name: profile.last_name,
          email: profile.email,
          phone: profile.phone,
          bank_account: profile.bank_account,
          profile_photo_url: profile.profile_photo_url
        })
        .eq('id', user.id)

      // Save theme to localStorage
      localStorage.setItem('theme', profile.theme)

      if (error) throw error

      // Update localStorage with new name
      const updatedUser = {
        ...user,
        name: `${profile.first_name} ${profile.last_name}`.trim(),
        email: profile.email
      }
      localStorage.setItem('user', JSON.stringify(updatedUser))
      setUser(updatedUser)

      setMessage({ type: 'success', text: 'Profil byl úspěšně uložen!' })
    } catch (err: any) {
      console.error('Error saving profile:', err)
      setMessage({ type: 'error', text: err.message || 'Nepodařilo se uložit profil' })
    } finally {
      setSaving(false)
    }
  }

  if (!user || loading) {
    return <div className="loading">Načítám...</div>
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Webomat CRM</h1>
        </div>
        <div className="header-right">
          <span className="user-info">
            {user.name} ({user.role === 'admin' ? 'Admin' : 'Obchodník'})
          </span>
          <button onClick={() => router.push('/dashboard')} className="btn-back">
            Zpět
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="profile-container">
          <h2>Můj profil</h2>
          <p className="profile-subtitle">Zde můžeš upravit své osobní údaje</p>

          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="first_name">Jméno</label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={profile.first_name}
                  onChange={handleChange}
                  placeholder="Vaše jméno"
                />
              </div>

              <div className="form-group">
                <label htmlFor="last_name">Příjmení</label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={profile.last_name}
                  onChange={handleChange}
                  placeholder="Vaše příjmení"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={profile.email}
                onChange={handleChange}
                placeholder="vas@email.cz"
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Telefon</label>
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
              <label htmlFor="bank_account">Číslo účtu</label>
              <input
                type="text"
                id="bank_account"
                name="bank_account"
                value={profile.bank_account}
                onChange={handleChange}
                placeholder="123456789/0100"
              />
              <span className="form-hint">Pro vyplácení provizí</span>
            </div>

            <div className="form-group">
              <label htmlFor="profile_photo">Profilová fotka</label>
              <input
                type="file"
                id="profile_photo"
                accept="image/*"
                onChange={handleFileChange}
              />
              {profile.profile_photo_url && (
                <img src={profile.profile_photo_url} alt="Profile" width={100} height={100} className="profile-photo" />
              )}
            </div>

            <div className="form-group">
              <label htmlFor="theme">Téma</label>
              <select
                id="theme"
                name="theme"
                value={profile.theme}
                onChange={handleChange}
              >
                <option value="light">Světlé</option>
                <option value="dark">Tmavé</option>
              </select>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-save" disabled={saving}>
                {saving ? 'Ukládám...' : 'Uložit změny'}
              </button>
            </div>
          </form>
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

        .profile-container h2 {
          margin: 0 0 0.5rem 0;
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

        @media (max-width: 600px) {
          .form-row {
            grid-template-columns: 1fr;
          }

          .profile-container {
            margin: 1rem;
            padding: 1.5rem;
          }
        }
      `}</style>
    </div>
  )
}
