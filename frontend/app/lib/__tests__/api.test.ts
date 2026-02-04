/**
 * Unit tests for ApiClient methods
 * Tests that all methods used throughout the frontend are properly defined
 */
import ApiClient from '../api'

// Mock axios to prevent actual network calls
jest.mock('axios')
const mockedAxios = require('axios')

describe('ApiClient Methods', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock localStorage for auth headers
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'mock-token'),
      },
      writable: true,
    })
  })

  describe('Authentication methods', () => {
    it('should have login method', () => {
      expect(typeof ApiClient.login).toBe('function')
    })
  })

  describe('CRM Business Management', () => {
    it('should have getBusinesses method', () => {
      expect(typeof ApiClient.getBusinesses).toBe('function')
    })

    it('should have getBusiness method', () => {
      expect(typeof ApiClient.getBusiness).toBe('function')
    })

    it('should have createBusiness method', () => {
      expect(typeof ApiClient.createBusiness).toBe('function')
    })

    it('should have updateBusiness method', () => {
      expect(typeof ApiClient.updateBusiness).toBe('function')
    })

    it('should have deleteBusiness method', () => {
      expect(typeof ApiClient.deleteBusiness).toBe('function')
    })

    it('should have getBusinessActivities method', () => {
      expect(typeof ApiClient.getBusinessActivities).toBe('function')
    })

    it('should have createActivity method', () => {
      expect(typeof ApiClient.createActivity).toBe('function')
    })

    it('should have getBusinessProjects method', () => {
      expect(typeof ApiClient.getBusinessProjects).toBe('function')
    })

    it('should have createProject method', () => {
      expect(typeof ApiClient.createProject).toBe('function')
    })

    it('should have getCRMStats method', () => {
      expect(typeof ApiClient.getCRMStats).toBe('function')
    })

    it('should have getCompanyFromARES method', () => {
      expect(typeof ApiClient.getCompanyFromARES).toBe('function')
    })
  })

  describe('User Profile Management', () => {
    it('should have getUserProfile method', () => {
      expect(typeof ApiClient.getUserProfile).toBe('function')
    })

    it('should have updateUserProfile method', () => {
      expect(typeof ApiClient.updateUserProfile).toBe('function')
    })

    it('should have updateUserLanguage method', () => {
      expect(typeof ApiClient.updateUserLanguage).toBe('function')
    })

    it('should have changePassword method', () => {
      expect(typeof ApiClient.changePassword).toBe('function')
    })

    it('should have uploadAvatar method', () => {
      expect(typeof ApiClient.uploadAvatar).toBe('function')
    })

    it('should have deleteAvatar method', () => {
      expect(typeof ApiClient.deleteAvatar).toBe('function')
    })
  })

  describe('Admin Management', () => {
    it('should have getUsers method', () => {
      expect(typeof ApiClient.getUsers).toBe('function')
    })

    it('should have toggleUserActive method', () => {
      expect(typeof ApiClient.toggleUserActive).toBe('function')
    })

    it('should have resetUserPassword method', () => {
      expect(typeof ApiClient.resetUserPassword).toBe('function')
    })

    it('should have getAdminDashboardStats method', () => {
      expect(typeof ApiClient.getAdminDashboardStats).toBe('function')
    })

    it('should have getSellerDashboard method', () => {
      expect(typeof ApiClient.getSellerDashboard).toBe('function')
    })

    it('should have getSellersList method', () => {
      expect(typeof ApiClient.getSellersList).toBe('function')
    })
  })

  describe('Web Project Management', () => {
    it('should have getWebProject method', () => {
      expect(typeof ApiClient.getWebProject).toBe('function')
    })

    it('should have updateWebProject method', () => {
      expect(typeof ApiClient.updateWebProject).toBe('function')
    })

    it('should have getWebProjectVersions method', () => {
      expect(typeof ApiClient.getWebProjectVersions).toBe('function')
    })

    it('should have createWebProjectVersion method', () => {
      expect(typeof ApiClient.createWebProjectVersion).toBe('function')
    })

    it('should have updateWebProjectVersion method', () => {
      expect(typeof ApiClient.updateWebProjectVersion).toBe('function')
    })

    it('should have deployVersion method', () => {
      expect(typeof ApiClient.deployVersion).toBe('function')
    })

    it('should have undeployVersion method', () => {
      expect(typeof ApiClient.undeployVersion).toBe('function')
    })

    it('should have captureScreenshot method', () => {
      expect(typeof ApiClient.captureScreenshot).toBe('function')
    })

    it('should have createShareLink method', () => {
      expect(typeof ApiClient.createShareLink).toBe('function')
    })

    it('should have getVersionComments method', () => {
      expect(typeof ApiClient.getVersionComments).toBe('function')
    })

    it('should have updateComment method', () => {
      expect(typeof ApiClient.updateComment).toBe('function')
    })

    it('should have markVersionAsCurrent method', () => {
      expect(typeof ApiClient.markVersionAsCurrent).toBe('function')
    })

    it('should have deleteVersion method', () => {
      expect(typeof ApiClient.deleteVersion).toBe('function')
    })

    it('should have deleteProject method', () => {
      expect(typeof ApiClient.deleteProject).toBe('function')
    })
  })

  describe('Website Generation', () => {
    it('should have generateWebsite method', () => {
      expect(typeof ApiClient.generateWebsite).toBe('function')
    })

    it('should have generateTestWebsite method', () => {
      expect(typeof ApiClient.generateTestWebsite).toBe('function')
    })

    it('should have deployTestWebsite method', () => {
      expect(typeof ApiClient.deployTestWebsite).toBe('function')
    })

    it('should have screenshotTestWebsite method', () => {
      expect(typeof ApiClient.screenshotTestWebsite).toBe('function')
    })
  })

  describe('Invoice Management', () => {
    it('should have getProjectInvoices method', () => {
      expect(typeof ApiClient.getProjectInvoices).toBe('function')
    })

    it('should have generateProjectInvoice method', () => {
      expect(typeof ApiClient.generateProjectInvoice).toBe('function')
    })

    it('should have updateInvoiceStatus method', () => {
      expect(typeof ApiClient.updateInvoiceStatus).toBe('function')
    })

    it('should have getInvoiceDetail method', () => {
      expect(typeof ApiClient.getInvoiceDetail).toBe('function')
    })

    it('should have generateInvoicePdf method', () => {
      expect(typeof ApiClient.generateInvoicePdf).toBe('function')
    })

    it('should have downloadInvoicePdf method', () => {
      expect(typeof ApiClient.downloadInvoicePdf).toBe('function')
    })

    it('should have generateReceivedInvoicePdf method', () => {
      expect(typeof ApiClient.generateReceivedInvoicePdf).toBe('function')
    })

    it('should have downloadReceivedInvoicePdf method', () => {
      expect(typeof ApiClient.downloadReceivedInvoicePdf).toBe('function')
    })

    it('should have getAdminInvoices method', () => {
      expect(typeof ApiClient.getAdminInvoices).toBe('function')
    })

    it('should have submitInvoiceForApproval method', () => {
      expect(typeof ApiClient.submitInvoiceForApproval).toBe('function')
    })

    it('should have approveInvoice method', () => {
      expect(typeof ApiClient.approveInvoice).toBe('function')
    })

    it('should have rejectInvoice method', () => {
      expect(typeof ApiClient.rejectInvoice).toBe('function')
    })

    it('should have getSellerClaims method', () => {
      expect(typeof ApiClient.getSellerClaims).toBe('function')
    })

    it('should have generatePaymentReminder method', () => {
      expect(typeof ApiClient.generatePaymentReminder).toBe('function')
    })

    it('should have sendPaymentReminder method', () => {
      expect(typeof ApiClient.sendPaymentReminder).toBe('function')
    })

    it('should have getSellerAccountLedger method', () => {
      expect(typeof ApiClient.getSellerAccountLedger).toBe('function')
    })
  })

  describe('Platform Feedback', () => {
    it('should have submitFeedback method', () => {
      expect(typeof ApiClient.submitFeedback).toBe('function')
    })

    it('should have getMyFeedback method', () => {
      expect(typeof ApiClient.getMyFeedback).toBe('function')
    })

    it('should have getAllFeedback method', () => {
      expect(typeof ApiClient.getAllFeedback).toBe('function')
    })

    it('should have updateFeedbackStatus method', () => {
      expect(typeof ApiClient.updateFeedbackStatus).toBe('function')
    })
  })

  describe('Public Preview', () => {
    it('should have getPreviewInfo method', () => {
      expect(typeof ApiClient.getPreviewInfo).toBe('function')
    })

    it('should have getPreviewHtml method', () => {
      expect(typeof ApiClient.getPreviewHtml).toBe('function')
    })

    it('should have addPreviewComment method', () => {
      expect(typeof ApiClient.addPreviewComment).toBe('function')
    })

    it('should have getPreviewComments method', () => {
      expect(typeof ApiClient.getPreviewComments).toBe('function')
    })
  })
})

describe('ApiClient Method Signatures', () => {
  // Test that critical methods have expected parameter signatures
  it('getBusiness should accept businessId parameter', () => {
    const mockResponse = { data: { id: '123', name: 'Test Business' } }
    mockedAxios.get.mockResolvedValue(mockResponse)
    
    expect(() => ApiClient.getBusiness('123')).not.toThrow()
    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/crm/businesses/123'),
      expect.objectContaining({ headers: expect.any(Object) })
    )
  })

  it('createBusiness should accept business data parameter', () => {
    const mockResponse = { data: { id: '123' } }
    mockedAxios.post.mockResolvedValue(mockResponse)
    
    const businessData = { name: 'Test Business', email: 'test@example.com' }
    expect(() => ApiClient.createBusiness(businessData)).not.toThrow()
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining('/crm/businesses'),
      businessData,
      expect.objectContaining({ headers: expect.any(Object) })
    )
  })

  it('toggleUserActive should accept userId parameter', () => {
    const mockResponse = { data: { message: 'User toggled' } }
    mockedAxios.put.mockResolvedValue(mockResponse)
    
    expect(() => ApiClient.toggleUserActive('user123')).not.toThrow()
    expect(mockedAxios.put).toHaveBeenCalledWith(
      expect.stringContaining('/admin/users/user123/toggle-active'),
      {},
      expect.objectContaining({ headers: expect.any(Object) })
    )
  })

  it('resetUserPassword should accept userId and optional newPassword', () => {
    const mockResponse = { data: { message: 'Password reset' } }
    mockedAxios.post.mockResolvedValue(mockResponse)
    
    expect(() => ApiClient.resetUserPassword('user123', 'newpass')).not.toThrow()
    expect(() => ApiClient.resetUserPassword('user123')).not.toThrow()
  })
})