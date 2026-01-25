import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useBusinessDetail } from '../useBusinessDetail'
import ApiClient from '../../../lib/api'

// Mock API client
vi.mock('../../lib/api', () => ({
  default: {
    getBusiness: vi.fn(),
    getBusinessActivities: vi.fn(),
    getBusinessProjects: vi.fn(),
    createProject: vi.fn(),
    updateProject: vi.fn(),
  },
}))

const mockApiClient = vi.mocked(ApiClient)

describe('useBusinessDetail - Project Creation', () => {
  const businessId = 'test-business-id'
  
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  it('should successfully create project and refresh data', async () => {
    // Arrange
    const mockBusiness = { id: businessId, name: 'Test Business' }
    const mockActivities = [{ id: 'act1', description: 'Test activity' }]
    const mockProjects = [{ id: 'proj1', name: 'Test Project' }]
    const mockNewProject = { id: 'proj2', name: 'New Project' }
    
    mockApiClient.getBusiness.mockResolvedValue(mockBusiness)
    mockApiClient.getBusinessActivities.mockResolvedValue(mockActivities)
    mockApiClient.getBusinessProjects.mockResolvedValue(mockProjects)
    mockApiClient.createProject.mockResolvedValue(mockNewProject)
    
    const { result } = renderHook(() => useBusinessDetail(businessId))
    
    // Wait for initial data load
    await waitFor(() => {
      expect(result.current.business).toEqual(mockBusiness)
      expect(result.current.loading).toBe(false)
    })
    
    // Act - create project
    const projectData = {
      package: 'start',
      status: 'offer',
      price_setup: 10000,
      price_monthly: 1000,
      domain: 'test.cz',
      notes: 'Test project',
    }
    
    await act(async () => {
      await result.current.handleSaveProject(projectData, false)
    })
    
    // Assert
    expect(mockApiClient.createProject).toHaveBeenCalledWith(businessId, projectData)
    expect(result.current.showProjectModal).toBe(false)
    expect(result.current.editingProject).toBe(null)
    expect(result.current.error).toBe('')
    
    // Verify data was refreshed
    await waitFor(() => {
      expect(mockApiClient.getBusinessProjects).toHaveBeenCalledTimes(2) // initial + refresh
      expect(result.current.projects).toContainEqual(mockNewProject)
    })
  })
  
  it('should handle project creation error without losing existing data', async () => {
    // Arrange
    const mockBusiness = { id: businessId, name: 'Test Business' }
    const mockActivities = [{ id: 'act1', description: 'Test activity' }]
    const mockProjects = [{ id: 'proj1', name: 'Test Project' }]
    
    mockApiClient.getBusiness.mockResolvedValue(mockBusiness)
    mockApiClient.getBusinessActivities.mockResolvedValue(mockActivities)
    mockApiClient.getBusinessProjects.mockResolvedValue(mockProjects)
    mockApiClient.createProject.mockRejectedValue({
      response: { status: 400, data: { detail: 'Validation error' } }
    })
    
    const { result } = renderHook(() => useBusinessDetail(businessId))
    
    await waitFor(() => {
      expect(result.current.business).toEqual(mockBusiness)
      expect(result.current.loading).toBe(false)
    })
    
    // Act - attempt to create project with invalid data
    const projectData = {
      package: 'invalid_package',
      status: 'invalid_status',
    }
    
    await act(async () => {
      await result.current.handleSaveProject(projectData, false)
    })
    
    // Assert - error occurred but data is preserved
    expect(result.current.error).toBe('[400] Validation error')
    expect(result.current.business).toEqual(mockBusiness) // Business data preserved
    expect(result.current.projects).toEqual(mockProjects) // Projects preserved
    expect(result.current.showProjectModal).toBe(true) // Modal stays open on error
  })
  
  it('should close modal after successful project creation even if refresh fails', async () => {
    // Arrange
    const mockBusiness = { id: businessId, name: 'Test Business' }
    const mockActivities = [{ id: 'act1', description: 'Test activity' }]
    const mockProjects = [{ id: 'proj1', name: 'Test Project' }]
    const mockNewProject = { id: 'proj2', name: 'New Project' }
    
    mockApiClient.getBusiness.mockResolvedValue(mockBusiness)
    mockApiClient.getBusinessActivities.mockResolvedValue(mockActivities)
    mockApiClient.getBusinessProjects.mockResolvedValue(mockProjects)
    
    // First call succeeds (project creation)
    // Second call fails (refresh projects)
    mockApiClient.createProject.mockResolvedValueOnce(mockNewProject)
    mockApiClient.getBusinessProjects.mockRejectedValueOnce(new Error('Network error'))
    
    const { result } = renderHook(() => useBusinessDetail(businessId))
    
    await waitFor(() => {
      expect(result.current.business).toEqual(mockBusiness)
    })
    
    // Act
    const projectData = {
      package: 'start',
      status: 'offer',
    }
    
    await act(async () => {
      await result.current.handleSaveProject(projectData, false)
    })
    
    // Assert - modal closed even though refresh failed
    expect(result.current.showProjectModal).toBe(false)
    expect(result.current.editingProject).toBe(null)
    expect(result.current.error).toBe('') // No error shown for refresh failure
    expect(result.current.business).toEqual(mockBusiness) // Original business data preserved
  })
  
  it('should successfully update existing project', async () => {
    // Arrange
    const mockBusiness = { id: businessId, name: 'Test Business' }
    const mockActivities = [{ id: 'act1', description: 'Test activity' }]
    const mockExistingProject = { id: 'proj1', name: 'Existing Project', package: 'start' }
    const mockUpdatedProject = { ...mockExistingProject, package: 'premium' }
    
    mockApiClient.getBusiness.mockResolvedValue(mockBusiness)
    mockApiClient.getBusinessActivities.mockResolvedValue(mockActivities)
    mockApiClient.getBusinessProjects.mockResolvedValue([mockExistingProject])
    mockApiClient.updateProject.mockResolvedValue(mockUpdatedProject)
    
    const { result } = renderHook(() => useBusinessDetail(businessId))
    
    await waitFor(() => {
      expect(result.current.business).toEqual(mockBusiness)
    })
    
    // Act - update project
    const updateData = {
      package: 'premium',
      status: 'won',
    }
    
    await act(async () => {
      await result.current.handleSaveProject(updateData, true, mockExistingProject.id)
    })
    
    // Assert
    expect(mockApiClient.updateProject).toHaveBeenCalledWith(mockExistingProject.id, updateData)
    expect(result.current.showProjectModal).toBe(false)
    expect(result.current.editingProject).toBe(null)
    expect(result.current.error).toBe('')
  })
  
  it('should prevent Not Found state by preserving business data during refresh errors', async () => {
    // Arrange
    const mockBusiness = { id: businessId, name: 'Test Business' }
    const mockActivities = [{ id: 'act1', description: 'Test activity' }]
    const mockProjects = [{ id: 'proj1', name: 'Test Project' }]
    const mockNewProject = { id: 'proj2', name: 'New Project' }
    
    // Initial load succeeds
    mockApiClient.getBusiness.mockResolvedValueOnce(mockBusiness)
    mockApiClient.getBusinessActivities.mockResolvedValueOnce(mockActivities)
    mockApiClient.getBusinessProjects.mockResolvedValueOnce(mockProjects)
    mockApiClient.createProject.mockResolvedValue(mockNewProject)
    
    // Refresh fails (simulating the bug scenario)
    mockApiClient.getBusiness.mockRejectedValueOnce(new Error('Business access lost'))
    
    const { result } = renderHook(() => useBusinessDetail(businessId))
    
    await waitFor(() => {
      expect(result.current.business).toEqual(mockBusiness)
    })
    
    // Act - create project
    const projectData = { package: 'start', status: 'offer' }
    
    await act(async () => {
      await result.current.handleSaveProject(projectData, false)
    })
    
    // Assert - business data is preserved, not null
    expect(result.current.business).toEqual(mockBusiness)
    expect(result.current.showProjectModal).toBe(false)
    expect(result.current.error).toBe('') // No error for refresh failure
    expect(result.current.loading).toBe(false)
  })
})