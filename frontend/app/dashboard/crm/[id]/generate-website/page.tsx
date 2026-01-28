'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import ApiClient from '../../../../lib/api'

interface WebsiteGenerationResult {
  html_content?: string
  html_content_en?: string
  message: string
  translation_status?: string
}

export default function WebsiteGenerationPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const projectId = searchParams.get('projectId')
  const businessId = searchParams.get('businessId')
  const businessName = searchParams.get('businessName') || 'Neznámá firma'
  
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<WebsiteGenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId || !businessId) {
      setError('Chybí parametry pro generování webu')
    }
  }, [projectId, businessId])

  const handleDryRun = async () => {
    if (!projectId) return
    
    setGenerating(true)
    setError(null)
    setResult(null)

    try {
      const response = await ApiClient.generateWebsite(projectId, {
        dry_run: true,
        include_english: 'no'
      })
      
      setResult(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při generování')
    } finally {
      setGenerating(false)
    }
  }

  const handleFullRun = async () => {
    if (!projectId) return
    
    setGenerating(true)
    setError(null)
    setResult(null)

    try {
      const response = await ApiClient.generateWebsite(projectId, {
        dry_run: false,
        include_english: 'auto'
      })
      
      setResult(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Chyba při generování')
    } finally {
      setGenerating(false)
    }
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h1 style={{ color: '#ef4444', marginBottom: '20px' }}>❌ Chyba</h1>
          <p style={{ color: '#666', marginBottom: '30px' }}>{error}</p>
          <button 
            onClick={() => router.back()} 
            className="btn-primary"
            style={{ padding: '12px 24px', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            Zpět
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container" style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px', borderBottom: '1px solid #e5e7eb', paddingBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#1f2937', marginBottom: '8px' }}>
              Generování webové stránky
            </h1>
            <p style={{ color: '#6b7280', fontSize: '16px' }}>
              Pro firmu: <strong>{businessName}</strong>
            </p>
          </div>
          <button 
            onClick={() => router.back()}
            style={{ padding: '10px 20px', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer' }}
          >
            ← Zpět
          </button>
        </div>
      </header>

      {!result && (
        <main>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '30px', marginBottom: '40px' }}>
            {/* DRY RUN Option */}
            <div style={{ 
              background: 'white', 
              border: '2px solid #e5e7eb', 
              borderRadius: '12px', 
              padding: '30px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
            }}>
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔧</div>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', marginBottom: '12px' }}>
                  DRY RUN Test
                </h3>
                <p style={{ color: '#6b7280', lineHeight: '1.6', marginBottom: '24px' }}>
                  Vygeneruje testovací webovou stránku bez volání AI API. 
                  Ideální pro testování funkčality a zobrazení výsledku.
                </p>
              </div>
              <button 
                onClick={handleDryRun}
                disabled={generating}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: generating ? '#9ca3af' : '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: generating ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {generating ? '⏳ Generuji...' : '🚀 Spustit DRY RUN'}
              </button>
            </div>

            {/* Full AI Generation Option */}
            <div style={{ 
              background: 'white', 
              border: '2px solid #e5e7eb', 
              borderRadius: '12px', 
              padding: '30px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
              opacity: 0.7,
              position: 'relative'
            }}>
              <div style={{ 
                position: 'absolute', 
                top: '10px', 
                right: '10px', 
                background: '#fbbf24', 
                color: '#92400e', 
                padding: '4px 8px', 
                borderRadius: '4px', 
                fontSize: '12px', 
                fontWeight: '600' 
              }}>
                BRZY DOSTUPNÉ
              </div>
              <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', marginBottom: '12px' }}>
                  AI Generování
                </h3>
                <p style={{ color: '#6b7280', lineHeight: '1.6', marginBottom: '24px' }}>
                  Plné generování pomocí Claude/GPT API s automatickým překladem. 
                  Vytvoří profesionální web s obsahem na míru.
                </p>
              </div>
              <button 
                disabled
                style={{
                  width: '100%',
                  padding: '16px',
                  background: '#d1d5db',
                  color: '#9ca3af',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'not-allowed'
                }}
              >
                Brzy dostupné
              </button>
            </div>
          </div>

          {generating && (
            <div style={{ textAlign: 'center', padding: '40px', background: '#f9fafb', borderRadius: '12px' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
              <h3 style={{ color: '#374151', marginBottom: '12px' }}>Generuji webovou stránku...</h3>
              <p style={{ color: '#6b7280' }}>Prosím, počkejte na dokončení procesu.</p>
            </div>
          )}
        </main>
      )}

      {result && (
        <main>
          <div style={{ marginBottom: '30px', padding: '20px', background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '8px' }}>
            <h3 style={{ color: '#166534', marginBottom: '8px' }}>✅ Generování dokončeno!</h3>
            <p style={{ color: '#15803d', marginBottom: '16px' }}>{result.message}</p>
            {result.translation_status && (
              <p style={{ color: '#6b7280', fontSize: '14px' }}>
                Stav překladu: {result.translation_status}
              </p>
            )}
          </div>

          {/* Website Preview */}
          {result.html_content && (
            <div style={{ marginBottom: '30px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', marginBottom: '20px' }}>
                🌐 Náhled vygenerovaného webu
              </h3>
              <div style={{ 
                border: '2px solid #e5e7eb', 
                borderRadius: '12px', 
                overflow: 'hidden',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
              }}>
                <iframe
                  srcDoc={result.html_content}
                  width="100%"
                  height="600"
                  style={{ border: 'none', display: 'block' }}
                  title="Generated Website Preview"
                />
              </div>
              
              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '15px', marginTop: '20px', justifyContent: 'center' }}>
                <button 
                  onClick={() => {
                    const blob = new Blob([result.html_content!], { type: 'text/html' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `website-${businessName.replace(/\s+/g, '-').toLowerCase()}.html`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                  style={{
                    padding: '12px 24px',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  📥 Stáhnout HTML
                </button>
                
                <button 
                  onClick={() => {
                    const newWindow = window.open()
                    if (newWindow) {
                      newWindow.document.write(result.html_content!)
                      newWindow.document.close()
                    }
                  }}
                  style={{
                    padding: '12px 24px',
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  🌐 Otevřít v novém okně
                </button>
                
                <button 
                  onClick={() => router.back()}
                  style={{
                    padding: '12px 24px',
                    background: '#f3f4f6',
                    color: '#374151',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  ← Zpět na CRM
                </button>
              </div>
            </div>
          )}

          {/* English Version */}
          {result.html_content_en && (
            <div style={{ marginBottom: '30px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', marginBottom: '20px' }}>
                🇬🇧 English Version
              </h3>
              <div style={{ 
                border: '2px solid #e5e7eb', 
                borderRadius: '12px', 
                overflow: 'hidden',
                boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
              }}>
                <iframe
                  srcDoc={result.html_content_en}
                  width="100%"
                  height="600"
                  style={{ border: 'none', display: 'block' }}
                  title="Generated Website Preview (English)"
                />
              </div>
            </div>
          )}

          {/* Generate Again */}
          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <button 
              onClick={() => {
                setResult(null)
                setError(null)
              }}
              style={{
                padding: '12px 24px',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              🔄 Generovat znovu
            </button>
          </div>
        </main>
      )}
    </div>
  )
}