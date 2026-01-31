'use client'

import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { ToastContainer } from './components/ui/ToastContainer'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ToastProvider>
        {children}
        <ToastContainer />
      </ToastProvider>
    </AuthProvider>
  )
}
