'use client'

import React, { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useToast } from '../../context/ToastContext'
import { AnimatedToast } from './AnimatedToast'

export function EnhancedToastContainer() {
  const { toasts, removeToast } = useToast()
  const [isMobile, setIsMobile] = useState(false)

  // Detect mobile vs desktop
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Container positioning classes
  const containerClasses = isMobile
    ? 'fixed bottom-6 left-1/2 transform -translate-x-1/2 z-[9999]'
    : 'fixed bottom-6 right-6 z-[9999]'

  // Container styles
  const containerStyles: React.CSSProperties = isMobile
    ? {
        display: 'flex',
        flexDirection: 'column' as const,
        alignItems: 'center',
        gap: '12px',
        width: '90vw',
        maxWidth: '320px'
      }
    : {
        display: 'flex',
        flexDirection: 'column' as const,
        alignItems: 'flex-end',
        gap: '12px',
        width: 'auto'
      }

  if (toasts.length === 0) {
    return null
  }

  return (
    <div
      className={containerClasses}
      style={containerStyles}
      role="alert"
      aria-live="polite"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <AnimatedToast
            key={toast.id}
            toast={toast}
            onRemove={removeToast}
            isVisible={true}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}