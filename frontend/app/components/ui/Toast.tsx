'use client'

import React, { useEffect } from 'react'
import { Toast, ToastType } from '../../context/ToastContext'

interface ToastProps {
  toast: Toast
  onRemove: (id: string) => void
}

export function ToastComponent({ toast, onRemove }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id)
    }, toast.duration || 3000)

    return () => clearTimeout(timer)
  }, [toast.id, toast.duration, onRemove])

  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'bg-green-500 border-green-600'
      case 'error':
        return 'bg-red-500 border-red-600'
      case 'warning':
        return 'bg-yellow-500 border-yellow-600'
      case 'info':
      default:
        return 'bg-blue-500 border-blue-600'
    }
  }

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return '✓'
      case 'error':
        return '✕'
      case 'warning':
        return '⚠'
      case 'info':
      default:
        return 'ℹ'
    }
  }

  return (
    <div
      className={`
        ${getToastStyles(toast.type)}
        text-white px-4 py-3 rounded-lg shadow-lg border
        flex items-center gap-3 min-w-[300px] max-w-md
        transform transition-all duration-300 ease-in-out
        animate-in slide-in-from-right-5 fade-in-0
        hover:scale-105 cursor-pointer
      `}
      onClick={() => onRemove(toast.id)}
    >
      <span className="text-xl font-bold">
        {getToastIcon(toast.type)}
      </span>
      <span className="flex-1 text-sm font-medium">
        {toast.message}
      </span>
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(toast.id)
        }}
        className="text-white hover:text-gray-200 transition-colors text-lg leading-none"
      >
        ×
      </button>
    </div>
  )
}