'use client'

import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { EnhancedToastContainer } from './components/ui/EnhancedToastContainer'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ToastProvider>
        {children}
        <EnhancedToastContainer />
      </ToastProvider>
    </AuthProvider>
  )
}
