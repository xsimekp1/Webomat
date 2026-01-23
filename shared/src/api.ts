import axios from 'axios'
import { API_BASE_URL } from './constants'
import type {
  User,
  Seller,
  Business,
  Activity,
  Project,
  CRMStats,
  TodayTask,
  SellerDashboard
} from './types'

// Platform-specific storage
let getAuthHeaders: () => Record<string, string>
let getStoredToken: () => Promise<string | null>
let setStoredToken: (token: string | null) => Promise<void>

// Initialize platform-specific functions
const initializePlatform = () => {
  // Check if we're in React Native (has AsyncStorage available)
  if (typeof navigator !== 'undefined' && navigator.product === 'ReactNative') {
    // React Native platform - will be set by mobile app
    getAuthHeaders = () => ({})
    getStoredToken = async () => null
    setStoredToken = async () => {}
  } else if (typeof window !== 'undefined') {
    // Web platform (Next.js)
    getAuthHeaders = () => {
      const token = localStorage.getItem('token')
      return token ? { 'Authorization': `Bearer ${token}` } : {}
    }
    getStoredToken = async () => localStorage.getItem('token')
    setStoredToken = async (token) => {
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    }
  } else {
    // Node.js/server platform
    getAuthHeaders = () => ({})
    getStoredToken = async () => null
    setStoredToken = async () => {}
  }
}

// Initialize on module load
initializePlatform()

class ApiClientClass {
  private getAuthHeaders() {
    return getAuthHeaders()
  }

  async getStoredToken() {
    return getStoredToken()
  }

  async setStoredToken(token: string | null) {
    return setStoredToken(token)
  }

  // Authentication
  async login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await axios.post(
      `${API_BASE_URL}/token`,
      formData,
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    )
    return response.data
  }

  async getUserProfile(): Promise<User> {
    const response = await axios.get(
      `${API_BASE_URL}/users/me`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async updateUserProfile(userData: any): Promise<User> {
    const response = await axios.post(
      `${API_BASE_URL}/users/me`,
      userData,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // Sellers
  async getSellersList(): Promise<Seller[]> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/sellers`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  // Businesses
  async getBusinesses(params?: {
    status_crm?: string
    search?: string
    assigned_to?: string
    page?: number
    limit?: number
  }): Promise<{ items: Business[]; total: number; page: number; limit: number }> {
    const queryParams = new URLSearchParams()
    if (params?.status_crm) queryParams.append('status_crm', params.status_crm)
    if (params?.search) queryParams.append('search', params.search)
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to)
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())

    const url = `${API_BASE_URL}/crm/businesses${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    const response = await axios.get(url, { headers: this.getAuthHeaders() })
    return response.data
  }

  async getBusiness(id: string): Promise<Business> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${id}`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async createBusiness(data: any): Promise<Business> {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses`,
      data,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  async updateBusiness(id: string, data: any): Promise<Business> {
    const response = await axios.put(
      `${API_BASE_URL}/crm/businesses/${id}`,
      data,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // Activities
  async getBusinessActivities(businessId: string): Promise<Activity[]> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${businessId}/activities`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async createActivity(businessId: string, data: any): Promise<Activity> {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses/${businessId}/activities`,
      data,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // Projects
  async getBusinessProjects(businessId: string): Promise<Project[]> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${businessId}/projects`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async createProject(businessId: string, data: any): Promise<Project> {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses/${businessId}/projects`,
      data,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  async updateProject(projectId: string, data: any): Promise<Project> {
    const response = await axios.put(
      `${API_BASE_URL}/crm/projects/${projectId}`,
      data,
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // Dashboard
  async getTodayTasks(): Promise<{ tasks: TodayTask[]; total: number }> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/dashboard/today`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async getCRMStats(): Promise<CRMStats> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/dashboard/stats`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async getSellerDashboard(): Promise<SellerDashboard> {
    const response = await axios.get(
      `${API_BASE_URL}/crm/seller/dashboard`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  // Website generation
  async generateWebsite(projectId: string, dryRun: boolean = false) {
    const response = await axios.post(
      `${API_BASE_URL}/website/generate`,
      { project_id: projectId, dry_run: dryRun },
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // ARES
  async getCompanyFromARES(ico: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/ares/${ico}`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  // Finance
  async getFinancialSummary() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/summary`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async getEarnings() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/earnings`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async changePassword(currentPassword: string, newPassword: string) {
    const response = await axios.post(
      `${API_BASE_URL}/users/me/password`,
      { current_password: currentPassword, new_password: newPassword },
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  // Admin
  async getUsers() {
    const response = await axios.get(
      `${API_BASE_URL}/admin/users`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async getUser(userId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/admin/users/${userId}`,
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }

  async resetUserPassword(userId: string, newPassword?: string) {
    const response = await axios.post(
      `${API_BASE_URL}/admin/users/${userId}/reset-password`,
      { new_password: newPassword || null },
      { headers: { ...this.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  async toggleUserActive(userId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/admin/users/${userId}/toggle-active`,
      {},
      { headers: this.getAuthHeaders() }
    )
    return response.data
  }
}

export const ApiClient = new ApiClientClass()
export default ApiClient