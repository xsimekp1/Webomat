'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useToast } from '../../context/ToastContext'
import { AnimatedToast } from './AnimatedToast'

export function EnhancedToastContainer() {
  const { toasts, removeToast } = useToast()
  const [isMobile, setIsMobile] = useState(false)
  const [mountedToasts, setMountedToasts] = useState<Set<string>>(new Set())

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
  const containerStyles = isMobile
    ? {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        width: '90vw',
        maxWidth: '320px'
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '12px',
        width: 'auto'
      }

  // Staggered animation for multiple toasts
  const containerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  // Handle toast lifecycle
  const handleToastMount = (toastId: string) => {
    setMountedToasts(prev => new Set(prev).add(toastId))
  }

  const handleToastUnmount = (toastId: string) => {
    setMountedToasts(prev => {
      const newSet = new Set(prev)
      newSet.delete(toastId)
      return newSet
    })
    removeToast(toastId)
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
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            layout
            onAnimationStart={() => handleToastMount(toast.id)}
            onAnimationComplete={() => {
              if (!mountedToasts.has(toast.id)) {
                handleToastUnmount(toast.id)
              }
            }}
          >
            <AnimatedToast
              toast={toast}
              onRemove={handleToastUnmount}
              isVisible={mountedToasts.has(toast.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}