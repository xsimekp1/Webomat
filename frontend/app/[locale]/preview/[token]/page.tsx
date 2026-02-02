'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import { useAuth } from '../../../../../context/AuthContext'

import { useToast } from '../../../context/ToastContext'
import ApiClient from '../../../../../lib/api'
import './styles.css'


interface PreviewInfo {
  version_id: string
  project_id: string
  version_number: number
  business_name: string | null
  domain: string | null
  has_html: boolean
}

interface Comment {
  id: string
  content: string
  author_name: string | null
  anchor_type: string | null
  anchor_x: number | null
  anchor_y: number | null
  created_at: string | null
}

export default function PreviewPage() {
  const params = useParams()
  const token = params.token as string
  const { showToast } = useToast()

  const [previewInfo, setPreviewInfo] = useState<PreviewInfo | null>(null)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Comment form state
  const [showCommentForm, setShowCommentForm] = useState(false)
  const [commentContent, setCommentContent] = useState('')
  const [authorName, setAuthorName] = useState('')
  const [authorEmail, setAuthorEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  // Honeypot field
  const [honeypot, setHoneypot] = useState('')

  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    const loadPreview = async () => {
      try {
        setLoading(true)

        // Load preview info
        const info = await ApiClient.getPreviewInfo(token)
        setPreviewInfo(info)

        // Load HTML content if available
        if (info.has_html) {
          const htmlData = await ApiClient.getPreviewHtml(token)
          setHtmlContent(htmlData.html_content)
        }

        // Load comments
        const commentsData = await ApiClient.getPreviewComments(token)
        setComments(commentsData)

      } catch (err: any) {
        const detail = err.response?.data?.detail
        if (detail) {
          setError(detail)
        } else {
          setError('Nepodarilo se nacist nahled')
        }
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      loadPreview()
    }
  }, [token])

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!commentContent.trim()) {
      showToast('Zadejte obsah komentare', 'warning')
      return
    }

    // Silent rejection for bots (honeypot field filled)
    if (honeypot) {
      setSubmitSuccess(true)
      setCommentContent('')
      setTimeout(() => setSubmitSuccess(false), 3000)
      return
    }

    setSubmitting(true)

    try {
      await ApiClient.addPreviewComment(token, {
        content: commentContent.trim(),
        author_name: authorName.trim() || undefined,
        author_email: authorEmail.trim() || undefined,
      })

      // Reload comments
      const commentsData = await ApiClient.getPreviewComments(token)
      setComments(commentsData)

      setCommentContent('')
      setSubmitSuccess(true)
      setTimeout(() => setSubmitSuccess(false), 3000)

    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Nepodarilo se odeslat komentar', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="preview-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Nacitam nahled...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="preview-page">
        <div className="error-state">
          <div className="error-icon">!</div>
          <h2>Nelze zobrazit nahled</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="preview-page">
      {/* Header */}
      <header className="preview-header">
        <div className="header-info">
          <h1>{previewInfo?.business_name || 'Nahled webu'}</h1>
          {previewInfo?.domain && (
            <span className="domain">{previewInfo.domain}</span>
          )}
          <span className="version">Verze {previewInfo?.version_number}</span>
        </div>
        <button
          className="btn-feedback"
          onClick={() => setShowCommentForm(!showCommentForm)}
        >
          {showCommentForm ? 'Skryt formular' : 'Zanechat komentar'}
        </button>
      </header>

      {/* Main content */}
      <div className="preview-content">
        {/* Website iframe */}
        <div className="preview-frame-container">
          {htmlContent ? (
            <iframe
              ref={iframeRef}
              srcDoc={htmlContent}
              className="preview-frame"
              title="Website Preview"
              sandbox="allow-scripts allow-same-origin"
            />
          ) : (
            <div className="no-preview">
              <p>Nahled neni k dispozici</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <aside className={`preview-sidebar ${showCommentForm ? 'open' : ''}`}>
          {/* Comment form */}
          {showCommentForm && (
            <div className="comment-form-section">
              <h3>Zanechat komentar</h3>

              {submitSuccess && (
                <div className="success-message">
                  Diky za Vas komentar!
                </div>
              )}

              <form onSubmit={handleSubmitComment}>
                <div className="form-group">
                  <label>Vase jmeno (volitelne)</label>
                  <input
                    type="text"
                    value={authorName}
                    onChange={(e) => setAuthorName(e.target.value)}
                    placeholder="Jan Novak"
                  />
                </div>

                <div className="form-group">
                  <label>E-mail (volitelne)</label>
                  <input
                    type="email"
                    value={authorEmail}
                    onChange={(e) => setAuthorEmail(e.target.value)}
                    placeholder="jan@example.com"
                  />
                </div>

                <div className="form-group">
                  <label>Vaše zpětná vazba *</label>
                  <textarea
                    value={commentContent}
                    onChange={(e) => setCommentContent(e.target.value)}
                    placeholder="Napiste svuj komentar k webu..."
                    rows={4}
                    required
                  />
                </div>

                {/* Honeypot field - hidden from users */}
                <input
                  type="text"
                  name="website"
                  value={honeypot}
                  onChange={(e) => setHoneypot(e.target.value)}
                  style={{ display: 'none' }}
                  tabIndex={-1}
                  autoComplete="off"
                />

                <button
                  type="submit"
                  className="btn-submit"
                  disabled={submitting}
                >
                  {submitting ? 'Odesilam...' : 'Odeslat komentar'}
                </button>
              </form>
            </div>
          )}

          {/* Comments list */}
          <div className="comments-section">
            <h3>Komentare ({comments.length})</h3>

            {comments.length === 0 ? (
              <p className="no-comments">Zatim zadne komentare</p>
            ) : (
              <div className="comments-list">
                {comments.map((comment) => (
                  <div key={comment.id} className="comment-item">
                    <div className="comment-header">
                      <span className="comment-author">
                        {comment.author_name || 'Anonymni'}
                      </span>
                      <span className="comment-date">
                        {comment.created_at
                          ? new Date(comment.created_at).toLocaleDateString('cs-CZ')
                          : ''}
                      </span>
                    </div>
                    <p className="comment-content">{comment.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="preview-footer">
        <p>
          Nahled vytvoren pomoci{' '}
          <a href="https://webomat.cz" target="_blank" rel="noopener noreferrer">
            Webomat
          </a>
        </p>
      </footer>
    </div>
  )
}
