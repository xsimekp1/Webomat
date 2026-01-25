import { useState, useCallback } from 'react'
import ApiClient from '../../lib/api'

export function useBusinessDetail(businessId: string) {
  const [business, setBusiness] = useState<any>(null)
  const [activities, setActivities] = useState<any[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [editingProject, setEditingProject] = useState<any>(null)
  const [saving, setSaving] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      console.log('🔄 [fetchData] Starting data fetch for business:', businessId)
      const [businessRes, activitiesRes, projectsRes] = await Promise.all([
        ApiClient.getBusiness(businessId),
        ApiClient.getBusinessActivities(businessId),
        ApiClient.getBusinessProjects(businessId),
      ])
      console.log('✅ [fetchData] Successfully fetched data:', {
        business: businessRes?.name,
        activitiesCount: activitiesRes?.length || 0,
        projectsCount: projectsRes?.length || 0
      })
      setBusiness(businessRes)
      setActivities(activitiesRes)
      setProjects(projectsRes || [])
    } catch (err: any) {
      console.error('❌ [fetchData] Error fetching data:', {
        businessId,
        status: err.response?.status,
        detail: err.response?.data?.detail,
        message: err.message
      })
      // Don't overwrite business state on partial failures - preserve existing data
      setError(err.response?.data?.detail || 'Chyba při načítání dat')
    } finally {
      setLoading(false)
    }
  }, [businessId])

  const handleSaveProject = useCallback(async (projectData: any, isEdit: boolean = false, projectId?: string) => {
    setSaving(true)
    setError('')

    try {
      console.log('🚀 [handleSaveProject] Starting project save:', { 
        businessId, 
        isEdit,
        data: projectData
      })
      
      let result
      if (isEdit && projectId) {
        result = await ApiClient.updateProject(projectId, projectData)
        console.log('✅ [handleSaveProject] Project updated:', result)
      } else {
        result = await ApiClient.createProject(businessId, projectData)
        console.log('✅ [handleSaveProject] Project created:', result)
      }
      
      // Close modal first to ensure UI updates
      setShowProjectModal(false)
      setEditingProject(null)
      
      // Refresh only projects list first - more targeted approach
      try {
        console.log('🔄 [handleSaveProject] Refreshing projects list...')
        const projectsRes = await ApiClient.getBusinessProjects(businessId)
        setProjects(projectsRes || [])
        console.log('✅ [handleSaveProject] Projects list refreshed:', projectsRes?.length || 0)
      } catch (projectErr: any) {
        console.error('⚠️ [handleSaveProject] Failed to refresh projects:', projectErr)
        // Don't show error for refresh failure - project was saved successfully
      }
      
      // Optionally refresh business data if needed
      try {
        console.log('🔄 [handleSaveProject] Refreshing business data...')
        const businessRes = await ApiClient.getBusiness(businessId)
        setBusiness(businessRes)
        console.log('✅ [handleSaveProject] Business data refreshed:', businessRes?.name)
      } catch (businessErr: any) {
        console.error('⚠️ [handleSaveProject] Failed to refresh business:', businessErr)
        // Don't show error for refresh failure - project was saved successfully
      }
      
    } catch (err: any) {
      console.error('❌ [handleSaveProject] Project save failed:', {
        status: err.response?.status,
        detail: err.response?.data?.detail,
        message: err.message
      })
      const detail = err.response?.data?.detail || err.message || 'Neznámá chyba'
      const status = err.response?.status || 'N/A'
      setError(`[${status}] ${detail}`)
    } finally {
      setSaving(false)
    }
  }, [businessId])

  return {
    business,
    activities,
    projects,
    loading,
    error,
    showProjectModal,
    editingProject,
    saving,
    setShowProjectModal,
    setEditingProject,
    fetchData,
    handleSaveProject,
  }
}