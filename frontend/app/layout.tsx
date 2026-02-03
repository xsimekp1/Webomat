import { redirect } from 'next/navigation'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Redirect to default locale
  redirect('/cs')
}
