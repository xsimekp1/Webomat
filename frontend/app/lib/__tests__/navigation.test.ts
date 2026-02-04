/**
 * Unit tests for navigation utilities
 * Tests getBackUrl function and localStorage navigation logic
 */
import { getBackUrl } from '../navigation'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value.toString()
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key]
    }),
    clear: jest.fn(() => {
      store = {}
    })
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
})

// Mock process.env
const originalEnv = process.env

describe('getBackUrl Navigation Logic', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.clear()
    process.env = { ...originalEnv, NODE_ENV: 'development' }
  })

  afterEach(() => {
    process.env = originalEnv
  })

  describe('Happy path - correct CRM page stored', () => {
    it('should return correct CRM page when localStorage contains full dashboard path', () => {
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/abc-123')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard/crm/abc-123')
      expect(localStorageMock.getItem).toHaveBeenCalledWith('lastCrmPage')
    })

    it('should return generic CRM page when different business ID is stored', () => {
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/xyz-789')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard/crm')
    })

    it('should normalize URL with missing dashboard prefix', () => {
      localStorageMock.setItem('lastCrmPage', '/crm/abc-123')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard/crm/abc-123')
    })

    it('should normalize URL without leading slash', () => {
      localStorageMock.setItem('lastCrmPage', 'dashboard/crm/abc-123')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard/crm/abc-123')
    })
  })

  describe('Edge cases and fallbacks', () => {
    it('should return default dashboard when localStorage is empty', () => {
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard')
      expect(localStorageMock.getItem).toHaveBeenCalledWith('lastCrmPage')
    })

    it('should return default dashboard when localStorage contains non-CRM page', () => {
      localStorageMock.setItem('lastCrmPage', '/dashboard/profile')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard')
    })

    it('should return default dashboard when localStorage contains malformed URL', () => {
      localStorageMock.setItem('lastCrmPage', 'not-a-valid-url')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard')
    })

    it('should handle missing business ID in localStorage', () => {
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/')
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard/crm')
    })

    it('should handle when window is undefined (server-side rendering)', () => {
      // Mock window as undefined
      const originalWindow = global.window
      delete (global as any).window
      
      const result = getBackUrl('abc-123')
      
      expect(result).toBe('/dashboard')
      
      // Restore window
      global.window = originalWindow
    })
  })

  describe('Error prevention scenarios', () => {
    it('should prevent 404 by always returning valid dashboard path', () => {
      // Test the exact scenario from the bug report
      localStorageMock.setItem('lastCrmPage', '/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      
      const result = getBackUrl('29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      
      // Should NOT return the incomplete URL that would cause 404
      expect(result).not.toBe('/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      // Should return the properly prefixed URL
      expect(result).toBe('/dashboard/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
    })

    it('should handle multiple business IDs correctly', () => {
      // First visit business A
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/business-a-id')
      
      // Navigate to project of business B
      const result = getBackUrl('business-b-id')
      
      // Should go to generic CRM, not try to navigate to business A's detail
      expect(result).toBe('/dashboard/crm')
    })

    it('should validate and fix the broken prefix issue', () => {
      // Simulate the exact bug scenario
      localStorageMock.setItem('lastCrmPage', '/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      
      const result = getBackUrl('29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      
      expect(result).toBe('/dashboard/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337')
      expect(result).not.toBe('/crm/29f53ab6-7c9b-4322-ac3f-abb44a5f5337') // 404-causing URL
    })
  })

  describe('Production vs Development behavior', () => {
    it('should not log in production environment', () => {
      process.env.NODE_ENV = 'production'
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/abc-123')
      
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      
      getBackUrl('abc-123')
      
      expect(consoleSpy).not.toHaveBeenCalled()
      
      consoleSpy.mockRestore()
    })

    it('should log in development environment', () => {
      process.env.NODE_ENV = 'development'
      localStorageMock.setItem('lastCrmPage', '/dashboard/crm/abc-123')
      
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
      
      getBackUrl('abc-123')
      
      expect(consoleSpy).toHaveBeenCalled()
      
      consoleSpy.mockRestore()
    })
  })
})

describe('getBackUrl Integration', () => {
  it('should handle real-world navigation scenarios', () => {
    // Scenario 1: Normal flow
    localStorageMock.setItem('lastCrmPage', '/dashboard/crm/user-123')
    
    let result = getBackUrl('user-123')
    expect(result).toBe('/dashboard/crm/user-123')
    
    // Scenario 2: Different project
    result = getBackUrl('user-456')
    expect(result).toBe('/dashboard/crm')
    
    // Scenario 3: No CRM history
    localStorageMock.setItem('lastCrmPage', '/dashboard/profile')
    result = getBackUrl('any-user')
    expect(result).toBe('/dashboard')
    
    // Scenario 4: Missing prefix (bug scenario)
    localStorageMock.setItem('lastCrmPage', '/crm/bug-id-123')
    result = getBackUrl('bug-id-123')
    expect(result).toBe('/dashboard/crm/bug-id-123')
  })
})