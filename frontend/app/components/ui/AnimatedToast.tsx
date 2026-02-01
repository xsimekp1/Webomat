'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Toast, ToastType } from '../../context/ToastContext'

interface AnimatedToastProps {
  toast: Toast
  onRemove: (id: string) => void
  isVisible: boolean
}

export function AnimatedToast({ toast, onRemove, isVisible }: AnimatedToastProps) {
  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          icon: '✓',
          iconBg: 'bg-white/20'
        }
      case 'error':
        return {
          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
          icon: '✕',
          iconBg: 'bg-white/20'
        }
      case 'warning':
        return {
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          icon: '⚠',
          iconBg: 'bg-white/20'
        }
      case 'info':
      default:
        return {
          background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
          icon: 'ℹ',
          iconBg: 'bg-white/20'
        }
    }
  }

  const styles = getToastStyles(toast.type)

  // Animation variants for desktop (slide from right)
  const desktopVariants = {
    initial: { 
      x: 400, 
      opacity: 0,
      scale: 0.8
    },
    animate: { 
      x: 0, 
      opacity: 1,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      x: 400, 
      opacity: 0,
      scale: 0.8,
      transition: {
        duration: 0.2,
        ease: "easeIn" as const
      }
    }
  }

  // Animation variants for mobile (slide from bottom)
  const mobileVariants = {
    initial: { 
      y: 100, 
      opacity: 0,
      scale: 0.9
    },
    animate: { 
      y: 0, 
      opacity: 1,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      y: 100, 
      opacity: 0,
      scale: 0.9,
      transition: {
        duration: 0.2,
        ease: "easeIn" as const
      }
    }
  }

  const variants = window.innerWidth >= 768 ? desktopVariants : mobileVariants

  return (
    <motion.div
      className={`
        relative overflow-hidden cursor-pointer
        backdrop-blur-md 
        shadow-2xl
        border border-white/20
        text-white
        px-4 py-3 
        rounded-2xl
        flex items-center gap-3 
        min-w-[320px] max-w-[400px]
        select-none
        transform-gpu
        will-change-transform
      `}
      style={{
        background: styles.background,
        boxShadow: `
          0 20px 25px -5px rgba(0, 0, 0, 0.1),
          0 10px 10px -5px rgba(0, 0, 0, 0.04),
          0 0 0 1px rgba(255, 255, 255, 0.1)
        `
      }}
      variants={variants}
      initial="initial"
      animate={isVisible ? "animate" : "initial"}
      exit="exit"
      onClick={() => onRemove(toast.id)}
      whileHover={{ 
        scale: 1.02,
        transition: { duration: 0.1 }
      }}
      whileTap={{ 
        scale: 0.98,
        transition: { duration: 0.1 }
      }}
    >
      {/* Icon */}
      <div className={`
        flex items-center justify-center
        w-8 h-8 rounded-full
        ${styles.iconBg}
        flex-shrink-0
      `}>
        <span className="text-lg font-bold leading-none">
          {styles.icon}
        </span>
      </div>

      {/* Message */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium leading-tight">
          {toast.message}
        </p>
      </div>

      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(toast.id)
        }}
        className="
          flex items-center justify-center
          w-6 h-6 rounded-full
          bg-white/10 hover:bg-white/20
          text-white/80 hover:text-white
          transition-colors duration-150
          flex-shrink-0
          text-sm leading-none
        "
      >
        ×
      </button>

      {/* Progress bar indicator */}
      {toast.duration && toast.duration > 0 && (
        <motion.div
          className="absolute bottom-0 left-0 h-1 bg-white/30"
          initial={{ width: "100%" }}
          animate={{ 
            width: "0%",
            transition: { duration: toast.duration / 1000, ease: "linear" }
          }}
        />
      )}
    </motion.div>
  )
}