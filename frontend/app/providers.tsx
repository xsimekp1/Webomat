'use client'

import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import { ToastProvider } from './context/ToastContext'
import { EnhancedToastContainer } from './components/ui/EnhancedToastContainer'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <LanguageProvider>
        <ToastProvider>
          {children}
          <EnhancedToastContainer />
        </ToastProvider>
      </LanguageProvider>
    </AuthProvider>
  )
}
