'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import ApiClient from '@/lib/api'
import { useToast } from '@/context/ToastContext'

type TabKey = 'brief' | 'structure' | 'brand' | 'constraints' | 'preview'

type SectionKey =
  | 'hero'
  | 'services'
  | 'how_it_works'
  | 'testimonials'
  | 'gallery'
  | 'about'
  | 'pricing'
  | 'faq'
  | 'contact'
  | 'footer'

type SectionConfig = {
  key: SectionKey
  label: string
  enabled: boolean
  note: string
}

type Inspiration = {
  url: string
  note: string
  strictness: 'close' | 'inspire'
}

type Constraints = {
  siteType: 'landing' | 'multipage'
  form: 'none' | 'simple' | 'quote'
  cookieBar: boolean
  seoBasics: boolean
  accessibilityBasics: boolean
  minimalJs: boolean
  hostingTarget: 'static' | 'vercel' | 'netlify'
}

type Brand = {
  brandName: string
  toneOfVoice: string
  primaryColor: string
  secondaryColor: string
  designStyle: 'modern' | 'corporate' | 'luxury' | 'friendly' | 'minimal'
  language: 'cs' | 'en' | 'auto'
  targetAudience: string
  font: 'inter' | 'source_sans' | 'lato'
}

type GenerateResponse = {
  message?: string
  html_content?: string
  html_content_en?: string
  translation_status?: string
}

const DEFAULT_SECTIONS: SectionConfig[] = [
  { key: 'hero', label: 'Hero', enabled: true, note: '' },
  { key: 'services', label: 'Služby', enabled: true, note: '' },
  { key: 'how_it_works', label: 'Jak to funguje', enabled: true, note: '' },
  { key: 'testimonials', label: 'Reference / Recenze', enabled: true, note: '' },
  { key: 'gallery', label: 'Galerie', enabled: true, note: '' },
  { key: 'about', label: 'O nás', enabled: true, note: '' },
  { key: 'pricing', label: 'Ceník', enabled: false, note: '' },
  { key: 'faq', label: 'FAQ', enabled: true, note: '' },
  { key: 'contact', label: 'Kontakt', enabled: true, note: '' },
  { key: 'footer', label: 'Footer', enabled: true, note: '' },
]

function clampMove<T>(arr: T[], from: number, to: number) {
  const next = [...arr]
  const item = next[from]
  next.splice(from, 1)
  next.splice(to, 0, item)
  return next
}

function Toggle({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
  hint?: string
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        padding: '12px 14px',
        borderRadius: 12,
        border: '1px solid #e5e7eb',
        background: checked ? 'rgba(16,185,129,0.10)' : 'white',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'all .15s ease',
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 900, color: '#111827', lineHeight: 1.2 }}>{label}</div>
        {hint ? (
          <div style={{ marginTop: 4, color: '#6b7280', fontSize: 12, lineHeight: 1.3 }}>
            {hint}
          </div>
        ) : null}
      </div>

      {/* switch */}
      <div
        style={{
          flex: '0 0 auto',
          width: 44,
          height: 26,
          borderRadius: 999,
          background: checked ? '#10b981' : '#e5e7eb',
          position: 'relative',
          transition: 'background .15s ease',
          boxShadow: 'inset 0 0 0 1px rgba(0,0,0,0.06)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 3,
            left: checked ? 22 : 3,
            width: 20,
            height: 20,
            borderRadius: 999,
            background: 'white',
            transition: 'left .15s ease',
            boxShadow: '0 2px 6px rgba(0,0,0,0.18)',
          }}
        />
      </div>
    </button>
  )
}

export default function GenerateWebsitePage() {
  const router = useRouter()
  const sp = useSearchParams()
  const { showToast } = useToast()

  const qpBusinessId = sp.get('businessId') || ''
  const qpProjectId = sp.get('projectId') || ''
  const qpBusinessName = sp.get('businessName') || ''
  const qpDryRun = sp.get('dryRun') === '1'

  // Kontext (přichází z CRM přes URL)
  const [businessId, setBusinessId] = useState(qpBusinessId)
  const [projectId, setProjectId] = useState(qpProjectId)
  const [businessName, setBusinessName] = useState(qpBusinessName)

  // UI
  const [tab, setTab] = useState<TabKey>('brief')
  const [error, setError] = useState<string>('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)

  // Deploy & Screenshot
  const [deploying, setDeploying] = useState(false)
  const [deployedUrl, setDeployedUrl] = useState<string | null>(null)
  const [capturingScreenshot, setCapturingScreenshot] = useState(false)
  const [screenshotUrl, setScreenshotUrl] = useState<string | null>(null)

  // Save version
  const [saving, setSaving] = useState(false)
  const [savedVersionId, setSavedVersionId] = useState<string | null>(null)

  // Zadání (request)
  const [exactCopy, setExactCopy] = useState('')
  const [flexibleCopy, setFlexibleCopy] = useState('')

  const [sections, setSections] = useState<SectionConfig[]>(DEFAULT_SECTIONS)

  const [inspirations, setInspirations] = useState<Inspiration[]>([
    { url: '', note: '', strictness: 'inspire' },
    { url: '', note: '', strictness: 'inspire' },
    { url: '', note: '', strictness: 'inspire' },
  ])

  const [brand, setBrand] = useState<Brand>({
    brandName: qpBusinessName || '',
    toneOfVoice: 'přátelský, profesionální, stručný',
    primaryColor: '#667eea',
    secondaryColor: '#10b981',
    designStyle: 'modern',
    language: 'cs',
    targetAudience: '',
    font: 'inter'
  })

  const [constraints, setConstraints] = useState<Constraints>({
    siteType: 'landing',
    form: 'simple',
    cookieBar: true,
    seoBasics: true,
    accessibilityBasics: true,
    minimalJs: true,
    hostingTarget: 'static',
  })

  const canGenerate = useMemo(() => !!projectId, [projectId])

  useEffect(() => {
    // jemná pomoc: když je businessName v URL a brandName je prázdný
    setBrand((b) => ({
      ...b,
      brandName: b.brandName || businessName || '',
    }))
  }, [businessName])

  // (volitelné) když někdo přijde s dryRun=1, můžeš rovnou navolit UI
  useEffect(() => {
    if (qpDryRun) {
      // pouze nastavíme tab, nic automaticky nespouštím (ať to není překvapení)
      setTab('preview')
    }
  }, [qpDryRun])

  const buildFuturePayloadPreview = () => {
    // To je “snapshot”, co později pošleš do backendu jako website_generation_request.
    // Zatím to jen ukazujeme v UI pro kontrolu.
    return {
      business_id: businessId || null,
      project_id: projectId || null,
      business_name: businessName || null,
      exact_copy: exactCopy,
      flexible_copy: flexibleCopy,
      sections: sections.map((s) => ({
        key: s.key,
        enabled: s.enabled,
        note: s.note || null,
      })),
      inspirations: inspirations
        .filter((x) => x.url.trim() || x.note.trim())
        .map((x) => ({
          url: x.url.trim(),
          note: x.note.trim(),
          strictness: x.strictness,
        })),
      brand,
      constraints,
      output_format: constraints.hostingTarget === 'static' ? 'static_html' : constraints.hostingTarget,
    }
  }

  const handleGenerate = async (dryRun: boolean) => {
    if (!canGenerate) {
      setError('Chybí projectId. Otevři to z CRM projektu (tlačítko Generovat web).')
      return
    }

    setGenerating(true)
    setError('')
    setResult(null)
    setDeployedUrl(null)
    setScreenshotUrl(null)
    setSavedVersionId(null)

    try {
      // ✅ DNEŠNÍ REALITA: backend už má /website/generate a ApiClient.generateWebsite(projectId, dryRun)
      // Později to nahradíš: ApiClient.generateWebsiteV2(payload) / createRequest+run+poll
      const resp = await ApiClient.generateWebsite(projectId, dryRun)

      // resp u vás typicky vrací { html_content, message, ... } (podle toho co už používáte jinde)
      setResult(resp || { message: 'Hotovo.' })
      setTab('preview')

      // Automatická změna statusu na "designováno" při úspěšném generování
      if (resp && businessId) {
        try {
          await ApiClient.updateBusinessStatus(businessId, 'designed')
          showToast('Status změněn na "Designováno"', 'success')
        } catch (statusError: any) {
          console.error('Failed to update business status:', statusError)
          // Nezobrazovat chybu uživateli, hlavní funkce (generování) proběhla úspěšně
        }
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Chyba při generování')
    } finally {
      setGenerating(false)
    }
  }

  const downloadHtml = (html: string, baseName: string) => {
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${baseName}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDeploy = async () => {
    if (!result?.html_content) return
    setDeploying(true)
    setError('')
    try {
      const response = await ApiClient.deployTestWebsite(result.html_content, businessName || 'Test')
      if (response.success && response.url) {
        setDeployedUrl(response.url)
      } else {
        setError(response.message || 'Nepodařilo se nasadit web')
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Chyba při nasazování')
    } finally {
      setDeploying(false)
    }
  }

  const handleScreenshot = async () => {
    if (!result?.html_content) return
    setCapturingScreenshot(true)
    setError('')
    try {
      const response = await ApiClient.screenshotTestWebsite(result.html_content, 'thumbnail')
      if (response.success && response.screenshot_url) {
        setScreenshotUrl(response.screenshot_url)
      } else {
        setError(response.message || 'Nepodařilo se pořídit screenshot')
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Chyba při pořizování screenshotu')
    } finally {
      setCapturingScreenshot(false)
    }
  }

  const handleSaveVersion = async () => {
    if (!result?.html_content || !projectId) return
    setSaving(true)
    setError('')
    try {
      const response = await ApiClient.createWebProjectVersion(projectId, {
        html_content: result.html_content,
        html_content_en: result.html_content_en || null,
        thumbnail_url: screenshotUrl || null,
        notes: `Vygenerováno ${new Date().toLocaleString('cs-CZ')}`
      })
      if (response.id) {
        setSavedVersionId(response.id)
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      // Handle Pydantic validation errors (array of objects) vs simple string errors
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '))
      } else if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Nepodařilo se uložit verzi')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>Automatizovaná tvorba webu</h1>
          <div style={{ color: '#6b7280', marginTop: 4 }}>
            Firma: <b>{businessName || '—'}</b> · Projekt: <b>{projectId || '—'}</b>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={() => router.back()}
            style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', fontWeight: 700 }}
          >
            ← Zpět
          </button>
          <button
            onClick={() => {
              setExactCopy('')
              setFlexibleCopy('')
              setSections(DEFAULT_SECTIONS)
              setInspirations([
                { url: '', note: '', strictness: 'inspire' },
                { url: '', note: '', strictness: 'inspire' },
                { url: '', note: '', strictness: 'inspire' },
              ])
              setBrand((b) => ({
                ...b,
                brandName: businessName || b.brandName,
              }))
              setConstraints({
                siteType: 'landing',
                form: 'simple',
                cookieBar: true,
                seoBasics: true,
                accessibilityBasics: true,
                minimalJs: true,
                hostingTarget: 'static',
              })
              setResult(null)
              setError('')
              setDeployedUrl(null)
              setScreenshotUrl(null)
              setSavedVersionId(null)
              setTab('brief')
            }}
            style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid #e5e7eb', background: '#f9fafb', cursor: 'pointer', fontWeight: 700 }}
          >
            Reset
          </button>
        </div>
      </div>

      {error ? (
        <div style={{ background: '#fee2e2', border: '1px solid #fecaca', color: '#991b1b', padding: 12, borderRadius: 10, marginBottom: 16 }}>
          {error}
        </div>
      ) : null}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
        {(['brief', 'structure', 'brand', 'constraints', 'preview'] as TabKey[]).map((k) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            style={{
              padding: '10px 14px',
              borderRadius: 10,
              border: '1px solid #e5e7eb',
              background: tab === k ? '#111827' : 'white',
              color: tab === k ? 'white' : '#374151',
              cursor: 'pointer',
              fontWeight: 800,
              fontSize: 13,
              textTransform: 'capitalize',
            }}
          >
            {k === 'brief' ? 'Brief' : k === 'structure' ? 'Struktura' : k === 'brand' ? 'Brand' : k === 'constraints' ? 'Funkce' : 'Preview'}
          </button>
        ))}
      </div>

      {/* Main layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 16, alignItems: 'start' }}>
        {/* Left: actions */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 14, padding: 14 }}>
          <div style={{ fontWeight: 900, marginBottom: 10 }}>Generování</div>

          <button
            onClick={() => handleGenerate(true)}
            disabled={!canGenerate || generating}
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: 10,
              border: 'none',
              background: !canGenerate || generating ? '#9ca3af' : '#667eea',
              color: 'white',
              fontWeight: 900,
              cursor: !canGenerate || generating ? 'not-allowed' : 'pointer',
              marginBottom: 10,
            }}
          >
            {generating ? '⏳ Generuji…' : '🔧 DRY RUN (bez AI)'}
          </button>

          <button
            onClick={() => handleGenerate(false)}
            disabled={!canGenerate || generating}
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: 10,
              border: '1px solid #d1d5db',
              background: 'white',
              color: '#111827',
              fontWeight: 900,
              cursor: !canGenerate || generating ? 'not-allowed' : 'pointer',
              opacity: generating ? 0.7 : 1,
            }}
            title="AI můžeš později gate-nout přes feature flag / permission"
          >
            🤖 AI Generování
          </button>

          <div style={{ height: 1, background: '#e5e7eb', margin: '14px 0' }} />

          <div style={{ fontWeight: 900, marginBottom: 8 }}>Snapshot zadání</div>
          <pre style={{ margin: 0, fontSize: 11, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 10, padding: 10, overflow: 'auto', maxHeight: 260 }}>
            {JSON.stringify(buildFuturePayloadPreview(), null, 2)}
          </pre>

          <div style={{ color: '#6b7280', fontSize: 12, marginTop: 10, lineHeight: 1.4 }}>
            Pozn.: zatím posíláme do backendu jen <code>project_id</code> + <code>dry_run</code>.
            Tenhle snapshot je připravený pro budoucí <i>website_generation_request</i>.
          </div>
        </div>

        {/* Right: tab content */}
        <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: 14, padding: 14 }}>
          {tab === 'brief' && (
            <>
              <h2 style={{ margin: '0 0 10px 0', fontSize: 16 }}>Brief</h2>

              <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Co musí být přesně (word-for-word)</label>
              <textarea
                value={exactCopy}
                onChange={(e) => setExactCopy(e.target.value)}
                rows={7}
                placeholder="H1 headline, disclaimers, přesné služby/ceník, přesné kontakty…"
                style={{ width: '100%', padding: 12, borderRadius: 10, border: '1px solid #d1d5db', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}
              />

              <div style={{ height: 12 }} />

              <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Text, který lze přeformulovat</label>
              <textarea
                value={flexibleCopy}
                onChange={(e) => setFlexibleCopy(e.target.value)}
                rows={7}
                placeholder="Popis firmy, služby, USP, tón komunikace…"
                style={{ width: '100%', padding: 12, borderRadius: 10, border: '1px solid #d1d5db' }}
              />

              <div style={{ height: 14 }} />

              <h3 style={{ margin: 0, fontSize: 14 }}>Inspirace (max 3)</h3>
              <div style={{ color: '#6b7280', fontSize: 12, marginTop: 4 }}>URL nestačí – napiš co konkrétně se ti líbí.</div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
                {inspirations.map((ins, i) => (
                  <div key={i} style={{ border: '1px solid #e5e7eb', borderRadius: 12, padding: 12 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 140px', gap: 10 }}>
                      <input
                        value={ins.url}
                        onChange={(e) => {
                          const v = e.target.value
                          setInspirations((prev) => prev.map((x, idx) => (idx === i ? { ...x, url: v } : x)))
                        }}
                        placeholder="https://inspirace.cz"
                        style={{ padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                      />
                      <select
                        value={ins.strictness}
                        onChange={(e) => {
                          const v = e.target.value as Inspiration['strictness']
                          setInspirations((prev) => prev.map((x, idx) => (idx === i ? { ...x, strictness: v } : x)))
                        }}
                        style={{ padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                      >
                        <option value="inspire">Jen inspirace</option>
                        <option value="close">Přiblížit styl</option>
                      </select>
                    </div>
                    <textarea
                      value={ins.note}
                      onChange={(e) => {
                        const v = e.target.value
                        setInspirations((prev) => prev.map((x, idx) => (idx === i ? { ...x, note: v } : x)))
                      }}
                      rows={3}
                      placeholder="Co se mi líbí (layout, barvy, menu, hero, sekce…)…"
                      style={{ width: '100%', marginTop: 10, padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                    />
                  </div>
                ))}
              </div>
            </>
          )}

          {tab === 'structure' && (
            <>
              <h2 style={{ margin: '0 0 10px 0', fontSize: 16 }}>Struktura webu</h2>
              <div style={{ color: '#6b7280', fontSize: 12, marginBottom: 10 }}>
                Zapnout/vypnout sekce a upravit pořadí (↑/↓).
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sections.map((s, idx) => (
                  <div key={s.key} style={{ display: 'grid', gridTemplateColumns: '26px 1fr 84px', gap: 10, alignItems: 'center', border: '1px solid #e5e7eb', borderRadius: 12, padding: 12 }}>
                    <input
                      type="checkbox"
                      checked={s.enabled}
                      onChange={(e) => {
                        const v = e.target.checked
                        setSections((prev) => prev.map((x, i) => (i === idx ? { ...x, enabled: v } : x)))
                      }}
                    />
                    <div>
                      <div style={{ fontWeight: 900 }}>{s.label}</div>
                      <input
                        value={s.note}
                        onChange={(e) => {
                          const v = e.target.value
                          setSections((prev) => prev.map((x, i) => (i === idx ? { ...x, note: v } : x)))
                        }}
                        placeholder="Poznámka pro AI (volitelné)"
                        style={{ width: '100%', marginTop: 6, padding: 10, borderRadius: 10, border: '1px solid #d1d5db', fontSize: 13 }}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => idx > 0 && setSections((prev) => clampMove(prev, idx, idx - 1))}
                        style={{ padding: '6px 8px', borderRadius: 10, border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer' }}
                        title="Nahoru"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => idx < sections.length - 1 && setSections((prev) => clampMove(prev, idx, idx + 1))}
                        style={{ padding: '6px 8px', borderRadius: 10, border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer' }}
                        title="Dolů"
                      >
                        ↓
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {tab === 'brand' && (
            <>
              <h2 style={{ margin: '0 0 10px 0', fontSize: 16 }}>Brand / styl</h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Název značky</label>
                  <input
                    value={brand.brandName}
                    onChange={(e) => setBrand((b) => ({ ...b, brandName: e.target.value }))}
                    style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Jazyk</label>
                  <select
                    value={brand.language}
                    onChange={(e) => setBrand((b) => ({ ...b, language: e.target.value as Brand['language'] }))}
                    style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                  >
                    <option value="cs">Čeština</option>
                    <option value="en">English</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>
                    Primární barva
                  </label>

                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>


                    {/* Color picker */}
                    <input
                      type="color"
                      value={brand.primaryColor || '#667eea'}
                      onChange={(e) => setBrand((b) => ({ ...b, primaryColor: e.target.value }))}
                      style={{
                        width: 44,
                        height: 38,
                        padding: 0,
                        borderRadius: 10,
                        border: '1px solid #d1d5db',
                        background: 'transparent',
                        cursor: 'pointer',
                      }}
                      aria-label="Vybrat primární barvu"
                    />

                    {/* Text input (hex) */}
                    <input
                      value={brand.primaryColor}
                      onChange={(e) => setBrand((b) => ({ ...b, primaryColor: e.target.value }))}
                      style={{ flex: 1, padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                      placeholder="#667eea"
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>
                    Sekundární barva
                  </label>

                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>


                    <input
                      type="color"
                      value={brand.secondaryColor || '#10b981'}
                      onChange={(e) => setBrand((b) => ({ ...b, secondaryColor: e.target.value }))}
                      style={{
                        width: 44,
                        height: 38,
                        padding: 0,
                        borderRadius: 10,
                        border: '1px solid #d1d5db',
                        background: 'transparent',
                        cursor: 'pointer',
                      }}
                      aria-label="Vybrat sekundární barvu"
                    />

                    <input
                      value={brand.secondaryColor}
                      onChange={(e) => setBrand((b) => ({ ...b, secondaryColor: e.target.value }))}
                      style={{ flex: 1, padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                      placeholder="#10b981"
                    />
                  </div>
                </div>
              </div>   

              <div>
                <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Font</label>
                <select
                  value={brand.font}
                  onChange={(e) => setBrand((b) => ({ ...b, font: e.target.value as Brand['font'] }))}
                  style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                >
                  <option value="inter">Inter — univerzální</option>
                  <option value="source_sans">Source Sans — profesionální</option>
                  <option value="lato">Lato — přívětivý</option>
                </select>
              </div>


              <div style={{ height: 12 }} />
              <div>
                <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Tone of voice</label>
                <input
                  value={brand.toneOfVoice}
                  onChange={(e) => setBrand((b) => ({ ...b, toneOfVoice: e.target.value }))}
                  style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                />
              </div>

              <div style={{ height: 12 }} />
              <div>

                <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Design styl</label>
                <select
                  value={brand.designStyle}
                  onChange={(e) => setBrand((b) => ({ ...b, designStyle: e.target.value as Brand['designStyle'] }))}
                  style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                >
                  <option value="modern">Modern</option>
                  <option value="corporate">Corporate</option>
                  <option value="luxury">Luxury</option>
                  <option value="friendly">Friendly</option>
                  <option value="minimal">Minimal</option>
                </select>
              </div>

              <div style={{ height: 12 }} />

              <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Cílová skupina (1–2 věty)</label>
              <textarea
                value={brand.targetAudience}
                onChange={(e) => setBrand((b) => ({ ...b, targetAudience: e.target.value }))}
                rows={3}
                style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
              />
            </>
          )}

          {tab === 'constraints' && (
            <>
              <h2 style={{ margin: '0 0 10px 0', fontSize: 16 }}>Funkce a omezení</h2>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Typ webu</label>
                  <select
                    value={constraints.siteType}
                    onChange={(e) => setConstraints((c) => ({ ...c, siteType: e.target.value as Constraints['siteType'] }))}
                    style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                  >
                    <option value="landing">Jednostránkový (landing)</option>
                    <option value="multipage">Vícestránkový</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Formulář</label>
                  <select
                    value={constraints.form}
                    onChange={(e) => setConstraints((c) => ({ ...c, form: e.target.value as Constraints['form'] }))}
                    style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
                  >
                    <option value="none">Žádný (jen tel/email)</option>
                    <option value="simple">Jednoduchý</option>
                    <option value="quote">Poptávkový</option>
                  </select>
                </div>
              </div>

              <div style={{ height: 12 }} />

              <label style={{ display: 'block', fontWeight: 800, marginBottom: 6 }}>Hosting target</label>
              <select
                value={constraints.hostingTarget}
                onChange={(e) => setConstraints((c) => ({ ...c, hostingTarget: e.target.value as Constraints['hostingTarget'] }))}
                style={{ width: '100%', padding: 10, borderRadius: 10, border: '1px solid #d1d5db' }}
              >
                <option value="static">Static export</option>
                <option value="vercel">Vercel</option>
                <option value="netlify">Netlify</option>
              </select>

              <div style={{ height: 12 }} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <Toggle
                  checked={constraints.cookieBar}
                  onChange={(v) => setConstraints((c) => ({ ...c, cookieBar: v }))}
                  label="Cookie lišta"
                  hint="Zatím placeholder / statický banner."
                />
                <Toggle
                  checked={constraints.seoBasics}
                  onChange={(v) => setConstraints((c) => ({ ...c, seoBasics: v }))}
                  label="SEO basics"
                  hint="Title/meta/OG + základní struktura."
                />
                <Toggle
                  checked={constraints.accessibilityBasics}
                  onChange={(v) => setConstraints((c) => ({ ...c, accessibilityBasics: v }))}
                  label="Přístupnost základ"
                  hint="Kontrast, focus states, aria-labely."
                />
                <Toggle
                  checked={constraints.minimalJs}
                  onChange={(v) => setConstraints((c) => ({ ...c, minimalJs: v }))}
                  label="Performance: minimal JS"
                  hint="Preferuj čisté HTML/CSS, bez těžkých skriptů."
                />
              </div>
            </>
          )}

          {tab === 'preview' && (
            <>
              <h2 style={{ margin: '0 0 10px 0', fontSize: 16 }}>Preview</h2>

              {!result ? (
                <div style={{ padding: 14, borderRadius: 12, border: '1px solid #e5e7eb', background: '#f9fafb', color: '#6b7280' }}>
                  Zatím nic nevygenerováno. Použij DRY RUN nebo AI.
                </div>
              ) : (
                <>
                  <div style={{ padding: 12, borderRadius: 12, border: '1px solid #bbf7d0', background: '#f0fdf4', marginBottom: 12 }}>
                    <div style={{ fontWeight: 900, color: '#166534' }}>✅ Hotovo</div>
                    <div style={{ color: '#15803d', marginTop: 6 }}>{result.message || 'OK'}</div>
                  </div>

                  {result.html_content ? (
                    <>
                      <div style={{ border: '1px solid #e5e7eb', borderRadius: 12, overflow: 'hidden' }}>
                        <iframe
                          sandbox="allow-same-origin"
                          srcDoc={result.html_content}
                          title="Preview"
                          style={{ width: '100%', height: 650, border: 'none', display: 'block' }}
                        />
                      </div>

                      <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
                        <button
                          onClick={() => {
  const slug = (businessName || 'business').trim().replace(/\s+/g, '-').toLowerCase()
  downloadHtml(result.html_content!, `website-${slug}`)
}}
                          style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: '#10b981', color: 'white', fontWeight: 900, cursor: 'pointer' }}
                        >
                          📥 Stáhnout HTML
                        </button>
                        <button
                          onClick={() => {
                            const w = window.open('', '_blank')
                            if (w) {
                              w.document.write(result.html_content!)
                              w.document.close()
                            }
                          }}
                          style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid #d1d5db', background: 'white', fontWeight: 900, cursor: 'pointer' }}
                        >
                          🌐 Otevřít v novém okně
                        </button>

                        {/* Deploy to Vercel button */}
                        <button
                          onClick={handleDeploy}
                          disabled={deploying}
                          style={{
                            padding: '10px 14px',
                            borderRadius: 10,
                            border: 'none',
                            background: deploying ? '#9ca3af' : '#3b82f6',
                            color: 'white',
                            fontWeight: 900,
                            cursor: deploying ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {deploying ? '⏳ Nasazuji...' : '🚀 Nasadit na Vercel'}
                        </button>

                        {/* Screenshot button */}
                        <button
                          onClick={handleScreenshot}
                          disabled={capturingScreenshot}
                          style={{
                            padding: '10px 14px',
                            borderRadius: 10,
                            border: '1px solid #d1d5db',
                            background: capturingScreenshot ? '#f3f4f6' : 'white',
                            fontWeight: 900,
                            cursor: capturingScreenshot ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {capturingScreenshot ? '⏳ Fotím...' : '📷 Screenshot'}
                        </button>

                        {/* Save Version button */}
                        <button
                          onClick={handleSaveVersion}
                          disabled={saving || !projectId}
                          style={{
                            padding: '10px 14px',
                            borderRadius: 10,
                            border: 'none',
                            background: saving ? '#9ca3af' : '#10b981',
                            color: 'white',
                            fontWeight: 900,
                            cursor: saving || !projectId ? 'not-allowed' : 'pointer',
                          }}
                        >
                          {saving ? '⏳ Ukládám...' : '💾 Uložit verzi'}
                        </button>
                      </div>

                      {/* Show deployed URL */}
                      {deployedUrl && (
                        <div style={{ marginTop: 12, padding: 12, borderRadius: 10, background: '#eff6ff', border: '1px solid #bfdbfe' }}>
                          <div style={{ fontWeight: 700, color: '#1e40af', marginBottom: 6 }}>🔗 Sdílitelný odkaz:</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                            <a
                              href={deployedUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: '#2563eb', wordBreak: 'break-all' }}
                            >
                              {deployedUrl}
                            </a>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(deployedUrl)
                              }}
                              style={{
                                padding: '4px 10px',
                                borderRadius: 6,
                                border: '1px solid #93c5fd',
                                background: 'white',
                                cursor: 'pointer',
                                fontWeight: 700,
                                fontSize: 12,
                              }}
                            >
                              📋 Kopírovat
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Show screenshot */}
                      {screenshotUrl && (
                        <div style={{ marginTop: 12 }}>
                          <div style={{ fontWeight: 700, marginBottom: 8 }}>📷 Náhled:</div>
                          <img
                            src={screenshotUrl}
                            alt="Screenshot"
                            style={{ maxWidth: 400, borderRadius: 8, border: '1px solid #e5e7eb', display: 'block' }}
                          />
                        </div>
                      )}

                      {/* Show saved version confirmation */}
                      {savedVersionId && (
                        <div style={{ marginTop: 12, padding: 12, borderRadius: 10, background: '#d1fae5', border: '1px solid #6ee7b7' }}>
                          <div style={{ fontWeight: 700, color: '#065f46' }}>✅ Verze uložena!</div>
                          <div style={{ color: '#047857', marginTop: 4 }}>
                            ID: {savedVersionId}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ padding: 14, borderRadius: 12, border: '1px solid #fecaca', background: '#fef2f2', color: '#991b1b' }}>
                      Backend nevrátil <code>html_content</code>.
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>

      <div style={{ marginTop: 14, fontSize: 12, color: '#9ca3af' }}>
        MVP: UI sbírá strukturovaný brief; aktuálně volá existující endpoint <code>/website/generate</code> přes <code>ApiClient.generateWebsite(projectId, dryRun)</code>.
        Další krok: vytvořit “request/run/version” endpointy a posílat payload snapshot do backendu.
      </div>
    </div>
  )
}
