'use client'

import { useState, useEffect } from 'react'
import ApiClient from '../../lib/api'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setContent('')
      setError(null)
      setSubmitted(false)
    }
  }, [isOpen])

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
        category: 'idea',
        priority: 'medium',
        page_url: window.location.href,
      })

      setSubmitted(true)
      setTimeout(() => {
        onClose()
      }, 1500)

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Nepodarilo se odeslat zpetnou vazbu')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!submitting) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="feedback-overlay" onClick={handleClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        {submitted ? (
          <div className="feedback-success">
            <div className="success-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p>Diky za Vasi zpetnou vazbu!</p>
          </div>
        ) : (
          <>
            <h3>Zpetna vazba</h3>

            {error && (
              <div className="feedback-error">{error}</div>
            )}

            <form onSubmit={handleSubmit}>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Popiste svuj napad, chybu nebo navrh na zlepseni..."
                rows={5}
                autoFocus
              />

              <div className="feedback-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={handleClose}
                  disabled={submitting}
                >
                  Zrusit
                </button>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={submitting}
                >
                  {submitting ? 'Odesilam...' : 'Odeslat'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>

      <style jsx>{`
        .feedback-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .feedback-modal {
          background: white;
          border-radius: 12px;
          padding: 24px;
          max-width: 450px;
          width: 100%;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        .feedback-modal h3 {
          margin: 0 0 16px 0;
          font-size: 18px;
          font-weight: 600;
          color: #374151;
        }

        .feedback-error {
          padding: 10px 12px;
          background: #fef2f2;
          color: #dc2626;
          border-radius: 6px;
          font-size: 14px;
          margin-bottom: 12px;
        }

        textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          font-size: 14px;
          font-family: inherit;
          resize: vertical;
          min-height: 120px;
        }

        textarea:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }

        textarea::placeholder {
          color: #9ca3af;
        }

        .feedback-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
          margin-top: 16px;
        }

        .btn-cancel {
          padding: 10px 20px;
          background: white;
          color: #374151;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }

        .btn-cancel:hover:not(:disabled) {
          background: #f9fafb;
          border-color: #d1d5db;
        }

        .btn-cancel:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-submit {
          padding: 10px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s;
        }

        .btn-submit:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-submit:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .feedback-success {
          text-align: center;
          padding: 24px 0;
        }

        .success-icon {
          width: 56px;
          height: 56px;
          background: #d1fae5;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 16px;
          color: #065f46;
        }

        .feedback-success p {
          margin: 0;
          font-size: 16px;
          font-weight: 500;
          color: #374151;
        }
      `}</style>
    </div>
  )
}
