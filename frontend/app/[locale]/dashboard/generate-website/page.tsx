import { Suspense } from 'react'
import GenerateWebsiteClient from './GenerateWebsiteClient'

export default function Page() {
  return (
    <Suspense fallback={<div style={{ padding: 24 }}>Načítám generátor…</div>}>
      <GenerateWebsiteClient />
    </Suspense>
  )
}