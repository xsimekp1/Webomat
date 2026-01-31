'use client'

import React from 'react'
import { useToast } from '../../context/ToastContext'
import { ToastComponent } from './Toast'

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastComponent toast={toast} onRemove={removeToast} />
        </div>
      ))}
    </div>
  )
}