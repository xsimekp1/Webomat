'use client'

import { useState } from 'react'
import { Modal, Button, Textarea, Select } from '../ui'
import ApiClient from '../../lib/api'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
}

const CATEGORIES = [
  { value: 'bug', label: 'Chyba / Bug' },
  { value: 'idea', label: 'Napad / Vylepseni' },
  { value: 'ux', label: 'Uzivatelsky zazit (UX)' },
  { value: 'other', label: 'Jine' },
]

const PRIORITIES = [
  { value: 'low', label: 'Nizka' },
  { value: 'medium', label: 'Stredni' },
  { value: 'high', label: 'Vysoka' },
]

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('idea')
  const [priority, setPriority] = useState('medium')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!content.trim() || content.trim().length < 10) {
      setError('Zpetna vazba musi mit alespon 10 znaku')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await ApiClient.submitFeedback({
        content: content.trim(),
        category: category as any,
        priority: priority as any,
        page_url: window.location.href,
      })

      setSubmitted(true)
      setTimeout(() => {
        setSubmitted(false)
        setContent('')
        setCategory('idea')
        setPriority('medium')
        onClose()
      }, 2000)

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodarilo se odeslat zpetnou vazbu')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!submitting) {
      setError(null)
      setSubmitted(false)
      onClose()
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Zpetna vazba" size="md">
      {submitted ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Diky za Vasi zpetnou vazbu!
          </h3>
          <p className="text-gray-600">
            Vase zprava byla uspesne odeslana.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-gray-600 mb-4">
            Pomozte nam zlepsit platformu. Podelte se o sve napady, nahlaste chyby nebo nam dejte vedet, co bychom mohli zlepsit.
          </p>

          {error && (
            <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Kategorie"
              options={CATEGORIES}
              value={category}
              onChange={(e: any) => setCategory(e.target.value)}
            />
            <Select
              label="Priorita"
              options={PRIORITIES}
              value={priority}
              onChange={(e: any) => setPriority(e.target.value)}
            />
          </div>

          <Textarea
            label="Vase zpetna vazba"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Popiste svuj napad, chybu nebo navrh na zlepseni..."
            rows={5}
            hint="Minimum 10 znaku"
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={submitting}
            >
              Zrusit
            </Button>
            <Button type="submit" loading={submitting}>
              Odeslat
            </Button>
          </div>
        </form>
      )}
    </Modal>
  )
}
