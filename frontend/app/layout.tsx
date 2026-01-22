import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Webomat CRM',
  description: 'CRM + Business Discovery System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="cs">
      <body>{children}</body>
    </html>
  )
}
