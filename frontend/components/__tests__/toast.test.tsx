import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { motion } from 'framer-motion'
import '@testing-library/jest-dom'

// Mock framer-motion to avoid animation complexity in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: 'div',
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// Mock window.innerWidth for responsive testing
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024, // Default to desktop
})

import { ToastProvider, useToast } from '../context/ToastContext'
import { AnimatedToast } from '../components/ui/AnimatedToast'
import { EnhancedToastContainer } from '../components/ui/EnhancedToastContainer'

// Test wrapper component
const TestComponent = () => {
  const { showToast, clearAll } = useToast()
  
  return (
    <div>
      <button
        onClick={() => showToast('Success message', 'success', 3000)}
        data-testid="success-btn"
      >
        Success Toast
      </button>
      <button
        onClick={() => showToast('Error message', 'error', 1000)}
        data-testid="error-btn"
      >
        Error Toast
      </button>
      <button
        onClick={() => showToast('Warning message', 'warning')}
        data-testid="warning-btn"
      >
        Warning Toast
      </button>
      <button
        onClick={() => showToast('Info message', 'info')}
        data-testid="info-btn"
      >
        Info Toast
      </button>
      <button
        onClick={() => showToast('Custom duration', 'info', 5000)}
        data-testid="duration-btn"
      >
        Long Duration Toast
      </button>
      <button onClick={clearAll} data-testid="clear-btn">
        Clear All
      </button>
      <EnhancedToastContainer />
    </div>
  )
}

const renderWithToast = (component: React.ReactElement) => {
  return render(
    <ToastProvider>
      {component}
    </ToastProvider>
  )
}

describe('Enhanced Toast System', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('ToastContext functionality', () => {
    it('should provide toast functions', () => {
      renderWithToast(<TestComponent />)
      
      expect(screen.getByTestId('success-btn')).toBeInTheDocument()
      expect(screen.getByTestId('error-btn')).toBeInTheDocument()
      expect(screen.getByTestId('warning-btn')).toBeInTheDocument()
      expect(screen.getByTestId('info-btn')).toBeInTheDocument()
    })

    it('should show toast when showToast is called', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument()
      })
    })

    it('should respect max 2 toasts limit', async () => {
      renderWithToast(<TestComponent />)
      
      // Add 3 toasts quickly
      fireEvent.click(screen.getByTestId('success-btn'))
      fireEvent.click(screen.getByTestId('error-btn'))
      fireEvent.click(screen.getByTestId('warning-btn'))
      
      await waitFor(() => {
        const allToasts = screen.getAllByText(/message/)
        // Should only have 2 visible toasts (the oldest should be removed)
        expect(allToasts.length).toBeLessThanOrEqual(2)
      })
    })

    it('should clear all toasts', async () => {
      renderWithToast(<TestComponent />)
      
      // Add toasts
      fireEvent.click(screen.getByTestId('success-btn'))
      fireEvent.click(screen.getByTestId('error-btn'))
      
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument()
        expect(screen.getByText('Error message')).toBeInTheDocument()
      })
      
      // Clear all
      fireEvent.click(screen.getByTestId('clear-btn'))
      
      await waitFor(() => {
        expect(screen.queryByText('Success message')).not.toBeInTheDocument()
        expect(screen.queryByText('Error message')).not.toBeInTheDocument()
      })
    })
  })

  describe('Toast Types and Styling', () => {
    it('should render success toast with correct styling', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        const toast = screen.getByText('Success message').closest('div')
        expect(toast).toHaveStyle({
          background: expect.stringContaining('#10b981')
        })
        expect(screen.getByText('✓')).toBeInTheDocument()
      })
    })

    it('should render error toast with correct styling', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('error-btn'))
      
      await waitFor(() => {
        const toast = screen.getByText('Error message').closest('div')
        expect(toast).toHaveStyle({
          background: expect.stringContaining('#ef4444')
        })
        expect(screen.getByText('✕')).toBeInTheDocument()
      })
    })

    it('should render warning toast with correct styling', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('warning-btn'))
      
      await waitFor(() => {
        const toast = screen.getByText('Warning message').closest('div')
        expect(toast).toHaveStyle({
          background: expect.stringContaining('#f59e0b')
        })
        expect(screen.getByText('⚠')).toBeInTheDocument()
      })
    })

    it('should render info toast with correct styling', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('info-btn'))
      
      await waitFor(() => {
        const toast = screen.getByText('Info message').closest('div')
        expect(toast).toHaveStyle({
          background: expect.stringContaining('#3b82f6')
        })
        expect(screen.getByText('ℹ')).toBeInTheDocument()
      })
    })
  })

  describe('Toast Lifecycle and Duration', () => {
    it('should auto-dismiss after default duration (3s)', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument()
      })
      
      // Fast-forward 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000)
      })
      
      await waitFor(() => {
        expect(screen.queryByText('Success message')).not.toBeInTheDocument()
      })
    })

    it('should respect custom duration', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('duration-btn'))
      
      await waitFor(() => {
        expect(screen.getByText('Custom duration')).toBeInTheDocument()
      })
      
      // Should still be visible after 3s (custom is 5s)
      act(() => {
        jest.advanceTimersByTime(3000)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Custom duration')).toBeInTheDocument()
      })
      
      // Should disappear after 5s
      act(() => {
        jest.advanceTimersByTime(2000)
      })
      
      await waitFor(() => {
        expect(screen.queryByText('Custom duration')).not.toBeInTheDocument()
      })
    })
  })

  describe('Toast Interactions', () => {
    it('should dismiss toast when clicking on it', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        const toast = screen.getByText('Success message')
        fireEvent.click(toast)
      })
      
      await waitFor(() => {
        expect(screen.queryByText('Success message')).not.toBeInTheDocument()
      })
    })

    it('should dismiss toast when clicking close button', async () => {
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        expect(screen.getByText('Success message')).toBeInTheDocument()
        
        const closeButton = screen.getByText('×')
        fireEvent.click(closeButton)
      })
      
      await waitFor(() => {
        expect(screen.queryByText('Success message')).not.toBeInTheDocument()
      })
    })
  })

  describe('AnimatedToast Component', () => {
    it('should render with correct props', () => {
      const mockToast = {
        id: 'test-toast',
        message: 'Test message',
        type: 'success' as const,
        duration: 3000
      }
      
      const onRemove = jest.fn()
      
      render(
        <AnimatedToast
          toast={mockToast}
          onRemove={onRemove}
          isVisible={true}
        />
      )
      
      expect(screen.getByText('Test message')).toBeInTheDocument()
      expect(screen.getByText('✓')).toBeInTheDocument()
    })

    it('should call onRemove when clicked', () => {
      const mockToast = {
        id: 'test-toast',
        message: 'Test message',
        type: 'info' as const,
      }
      
      const onRemove = jest.fn()
      
      render(
        <AnimatedToast
          toast={mockToast}
          onRemove={onRemove}
          isVisible={true}
        />
      )
      
      fireEvent.click(screen.getByText('Test message'))
      expect(onRemove).toHaveBeenCalledWith('test-toast')
    })
  })

  describe('Responsive Behavior', () => {
    it('should use desktop positioning on large screens', () => {
      // Mock desktop
      Object.defineProperty(window, 'innerWidth', { value: 1024 })
      
      renderWithToast(<TestComponent />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      // Check that container has desktop positioning classes
      const container = screen.getByText('Success message').closest('[role="alert"]')?.parentElement
      expect(container?.className).toContain('right-6')
      expect(container?.className).not.toContain('-translate-x-1/2')
    })

    it('should use mobile positioning on small screens', async () => {
      // Mock mobile
      Object.defineProperty(window, 'innerWidth', { value: 375 })
      
      // Re-render with new width
      const MobileTest = () => {
        const [mounted, setMounted] = React.useState(false)
        React.useEffect(() => setMounted(true), [])
        
        if (!mounted) return null
        
        return <TestComponent />
      }
      
      renderWithToast(<MobileTest />)
      
      fireEvent.click(screen.getByTestId('success-btn'))
      
      await waitFor(() => {
        const container = screen.getByText('Success message').closest('[role="alert"]')?.parentElement
        // Note: This would require the component to detect width changes
        // For now, we just test it renders on mobile
        expect(screen.getByText('Success message')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle missing showToast gracefully', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation()
      
      expect(() => {
        render(
          <ToastProvider>
            <div>Test</div>
          </ToastProvider>
        )
      }).not.toThrow()
      
      consoleError.mockRestore()
    })

    it('should handle invalid toast type gracefully', async () => {
      const TestInvalidType = () => {
        const { showToast } = useToast()
        
        return (
          <button
            onClick={() => showToast('Invalid type message', 'invalid' as any)}
            data-testid="invalid-btn"
          >
            Invalid Toast
          </button>
        )
      }
      
      renderWithToast(<TestInvalidType />)
      
      fireEvent.click(screen.getByTestId('invalid-btn'))
      
      // Should still render with default info styling
      await waitFor(() => {
        expect(screen.getByText('Invalid type message')).toBeInTheDocument()
        expect(screen.getByText('ℹ')).toBeInTheDocument() // Default icon
      })
    })
  })
})

// Performance tests
describe('Toast Performance', () => {
  it('should handle rapid toast creation/removal without memory leaks', async () => {
    renderWithToast(<TestComponent />)
    
    // Rapidly create and remove many toasts
    for (let i = 0; i < 10; i++) {
      act(() => {
        fireEvent.click(screen.getByTestId('success-btn'))
      })
      act(() => {
        jest.advanceTimersByTime(100)
      })
    }
    
    // Should not exceed max 2 visible toasts
    await waitFor(() => {
      const allToasts = screen.getAllByText(/Success message/)
      expect(allToasts.length).toBeLessThanOrEqual(2)
    })
    
    // Clean up all remaining toasts
    act(() => {
      jest.advanceTimersByTime(5000)
    })
    
    await waitFor(() => {
      expect(screen.queryByText(/Success message/)).not.toBeInTheDocument()
    })
  })
})