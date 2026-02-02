'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import ApiClient from '@/lib/api'
import { Button, Badge, Card, Select } from '@/components/ui'

interface Feedback {
  id: string
  submitted_by: string
  submitter_name: string | null
  content: string
  category: string
  priority: string
  status: string
  admin_note: string | null
  handled_by: string | null
  handler_name: string | null
  handled_at: string | null
  page_url: string | null
  created_at: string | null
}

const CATEGORY_LABELS: Record<string, string> = {
  bug: 'Chyba',
  idea: 'Napad',
  ux: 'UX',
  other: 'Jine',
}

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Nizka',
  medium: 'Stredni',
  high: 'Vysoka',
}

const STATUS_LABELS: Record<string, string> = {
  open: 'Otevreno',
  in_progress: 'Reseno',
  done: 'Hotovo',
  rejected: 'Zamitnuto',
}

const STATUS_VARIANTS: Record<string, 'default' | 'warning' | 'success' | 'danger'> = {
  open: 'default',
  in_progress: 'warning',
  done: 'success',
  rejected: 'danger',
}

const PRIORITY_VARIANTS: Record<string, 'default' | 'warning' | 'danger'> = {
  low: 'default',
  medium: 'warning',
  high: 'danger',
}

export default function AdminFeedbackPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { showToast } = useToast()
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editStatus, setEditStatus] = useState<string>('')
  const [editNote, setEditNote] = useState<string>('')
  const [saving, setSaving] = useState(false)

  // Check admin access
  useEffect(() => {
    if (user && user.role !== 'admin') {
      router.push('/dashboard')
    }
  }, [user, router])

  const loadFeedbacks = useCallback(async () => {
    try {
      setLoading(true)
      const params: any = {}
      if (statusFilter !== 'all') params.status = statusFilter
      if (categoryFilter !== 'all') params.category = categoryFilter

      const data = await ApiClient.getAllFeedback(params)
      setFeedbacks(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodarilo se nacist zpetnou vazbu')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, categoryFilter])

  useEffect(() => {
    loadFeedbacks()
  }, [loadFeedbacks])

  const handleEdit = (feedback: Feedback) => {
    setEditingId(feedback.id)
    setEditStatus(feedback.status)
    setEditNote(feedback.admin_note || '')
  }

  const handleSave = async (id: string) => {
    setSaving(true)
    try {
      await ApiClient.updateFeedbackStatus(id, {
        status: editStatus,
        admin_note: editNote || undefined,
      })
      setEditingId(null)
      loadFeedbacks()
      showToast('Zmeny byly ulozeny', 'success')
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se ulozit zmeny', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setEditStatus('')
    setEditNote('')
  }

  if (user?.role !== 'admin') {
    return null
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Zpetna vazba</h1>
        <p className="text-gray-600">Sprava zpetne vazby od uzivatelu platformy</p>
      </div>

      {/* Filters */}
      <Card className="mb-6" padding="md">
        <div className="flex flex-wrap gap-4">
          <div className="w-48">
            <Select
              label="Status"
              value={statusFilter}
              onChange={(e: any) => setStatusFilter(e.target.value)}
              options={[
                { value: 'all', label: 'Vsechny' },
                { value: 'open', label: 'Otevreno' },
                { value: 'in_progress', label: 'Reseno' },
                { value: 'done', label: 'Hotovo' },
                { value: 'rejected', label: 'Zamitnuto' },
              ]}
            />
          </div>
          <div className="w-48">
            <Select
              label="Kategorie"
              value={categoryFilter}
              onChange={(e: any) => setCategoryFilter(e.target.value)}
              options={[
                { value: 'all', label: 'Vsechny' },
                { value: 'bug', label: 'Chyba' },
                { value: 'idea', label: 'Napad' },
                { value: 'ux', label: 'UX' },
                { value: 'other', label: 'Jine' },
              ]}
            />
          </div>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Nacitam...
        </div>
      ) : feedbacks.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          Žádná zpětná vazba
        </div>
      ) : (
        <div className="space-y-4">
          {feedbacks.map((feedback) => (
            <Card key={feedback.id} padding="md" variant="bordered">
              <div className="flex flex-wrap justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <Badge variant={STATUS_VARIANTS[feedback.status] || 'default'}>
                    {STATUS_LABELS[feedback.status] || feedback.status}
                  </Badge>
                  <Badge variant={PRIORITY_VARIANTS[feedback.priority] || 'default'} size="sm">
                    {PRIORITY_LABELS[feedback.priority] || feedback.priority}
                  </Badge>
                  <Badge variant="purple" size="sm">
                    {CATEGORY_LABELS[feedback.category] || feedback.category}
                  </Badge>
                </div>
                <div className="text-sm text-gray-500">
                  {feedback.created_at
                    ? new Date(feedback.created_at).toLocaleString('cs-CZ')
                    : ''}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-gray-800 whitespace-pre-wrap">{feedback.content}</p>
              </div>

              <div className="flex flex-wrap justify-between items-center gap-4 pt-4 border-t border-gray-100">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{feedback.submitter_name || 'Neznamy'}</span>
                  {feedback.page_url && (
                    <span className="ml-2 text-gray-400">
                      z {new URL(feedback.page_url).pathname}
                    </span>
                  )}
                </div>

                {editingId === feedback.id ? (
                  <div className="flex items-center gap-3">
                    <select
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                      className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm"
                    >
                      <option value="open">Otevreno</option>
                      <option value="in_progress">Reseno</option>
                      <option value="done">Hotovo</option>
                      <option value="rejected">Zamitnuto</option>
                    </select>
                    <input
                      type="text"
                      value={editNote}
                      onChange={(e) => setEditNote(e.target.value)}
                      placeholder="Poznamka..."
                      className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm w-48"
                    />
                    <Button size="sm" onClick={() => handleSave(feedback.id)} loading={saving}>
                      Ulozit
                    </Button>
                    <Button size="sm" variant="ghost" onClick={handleCancel}>
                      Zrusit
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    {feedback.admin_note && (
                      <span className="text-sm text-gray-500 italic">
                        "{feedback.admin_note}"
                      </span>
                    )}
                    {feedback.handler_name && (
                      <span className="text-sm text-gray-500">
                        Resil: {feedback.handler_name}
                      </span>
                    )}
                    <Button size="sm" variant="secondary" onClick={() => handleEdit(feedback)}>
                      Upravit
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
