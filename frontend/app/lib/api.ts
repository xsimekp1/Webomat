import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private static getAuthHeaders() {
    if (typeof window === 'undefined') return {};
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  // Autentizační endpointy
  static async login(username: string, password: string) {
    // Use OAuth2 form format for /token endpoint
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(
      `${API_BASE_URL}/token`,
      formData,
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    return response.data;
  }

  static async getSellerAccountLedger(params: { range: string; type: string; status: string }) {
    const queryParams = new URLSearchParams()

    queryParams.append('range', params.range)
    if (params.type !== 'all') queryParams.append('type', params.type)
    if (params.status !== 'all') queryParams.append('status', params.status)

    const url = `${API_BASE_URL}/seller/account/ledger${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    const response = await axios.get(url, { headers: ApiClient.getAuthHeaders() })
    return response.data
  }

  static async getUserProfile() {
    const response = await axios.get(
      `${API_BASE_URL}/users/me`,
      { headers: ApiClient.getAuthHeaders() }
    )
    return response.data
  }

  static async updateUserProfile(userData: any) {
    const response = await axios.post(
      `${API_BASE_URL}/users/me`,
      userData,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
    return response.data
  }

  static async uploadAvatar(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(
      `${API_BASE_URL}/upload/avatar`,
      formData,
      {
        headers: {
          ...ApiClient.getAuthHeaders(),
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    return response.data;
  }

  // Invoice reminders
  static async generatePaymentReminder(invoiceId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/invoices/${invoiceId}/generate-reminder`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async sendPaymentReminder(invoiceId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/invoices/${invoiceId}/send-reminder`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async deleteAvatar() {
    const response = await axios.delete(
      `${API_BASE_URL}/upload/avatar`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // CRM - ARES API
  static async getCompanyFromARES(ico: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/ares/${ico}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // CRM endpointy - Businesses
  static async getBusinesses(params?: {
    status_crm?: string;
    search?: string;
    assigned_to?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.status_crm) queryParams.append('status_crm', params.status_crm);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.assigned_to) queryParams.append('assigned_to', params.assigned_to);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `${API_BASE_URL}/crm/businesses${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await axios.get(url, { headers: ApiClient.getAuthHeaders() });
    return response.data;
  }

  static async getBusiness(id: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${id}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createBusiness(data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async updateBusiness(id: string, data: any) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/businesses/${id}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async deleteBusiness(id: string) {
    const response = await axios.delete(
      `${API_BASE_URL}/crm/businesses/${id}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // CRM - Activities
  static async getBusinessActivities(businessId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${businessId}/activities`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createActivity(businessId: string, data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses/${businessId}/activities`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // CRM - Projects
  static async getBusinessProjects(businessId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${businessId}/projects`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createProject(businessId: string, data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/businesses/${businessId}/projects`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async updateProject(projectId: string, data: any) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/projects/${projectId}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // CRM - Dashboard
  static async getTodayTasks() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/dashboard/today`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getCRMStats() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/dashboard/stats`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // Business a project listing pro generátor
  static async listBusinesses() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses`,
      { 
        headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' },
        params: { limit: 100, include_projects: true }
      }
    );
    return response.data;
  }

  static async listProjectsForBusiness(businessId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/businesses/${businessId}/projects`,
      { 
        headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' }
      }
    );
    return response.data;
  }

  static async generateWebsiteV2(payload: any) {
    const response = await axios.post(
      `${API_BASE_URL}/website/generate-v2`,
      payload,
      { 
        headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' }
      }
    );
    return response.data;
  }

  // Finance endpointy
  static async getFinancialSummary() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/summary`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getFinancialAccounts() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/accounts`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createFinancialAccount(accountData: any) {
    const response = await axios.post(
      `${API_BASE_URL}/financial/accounts`,
      accountData,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getEarnings() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/earnings`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createEarning(earningData: any) {
    const response = await axios.post(
      `${API_BASE_URL}/financial/earnings`,
      earningData,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getPayouts() {
    const response = await axios.get(
      `${API_BASE_URL}/financial/payouts`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createPayout(payoutData: any) {
    const response = await axios.post(
      `${API_BASE_URL}/financial/payouts`,
      payoutData,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // Password management
  static async changePassword(currentPassword: string, newPassword: string) {
    const response = await axios.post(
      `${API_BASE_URL}/users/me/password`,
      { current_password: currentPassword, new_password: newPassword },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // Admin endpointy
  static async getUsers() {
    const response = await axios.get(
      `${API_BASE_URL}/admin/users`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getUser(userId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/admin/users/${userId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async resetUserPassword(userId: string, newPassword?: string) {
    const response = await axios.post(
      `${API_BASE_URL}/admin/users/${userId}/reset-password`,
      { new_password: newPassword || null },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async toggleUserActive(userId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/admin/users/${userId}/toggle-active`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getAdminDashboardStats() {
    const response = await axios.get(
      `${API_BASE_URL}/admin/dashboard/stats`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getSellerDashboard() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/seller/dashboard`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async generateTestWebsite(
    dryRun: boolean = true,
    businessName?: string,
    businessType?: string,
    includeEnglish: 'no' | 'auto' | 'client' = 'no'
  ) {
    const response = await axios.post(
      `${API_BASE_URL}/website/generate-test`,
      {
        dry_run: dryRun,
        business_name: businessName || 'Test Firma s.r.o.',
        business_type: businessType || 'restaurace',
        include_english: includeEnglish
      },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // Website Generation endpointy
  static async generateWebsite(projectId: string, dryRun: boolean = false) {
    const response = await axios.post(
      `${API_BASE_URL}/website/generate`,
      { project_id: projectId, dry_run: dryRun },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // Website Versions
  static async getWebsiteVersions(projectId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/projects/${projectId}/versions`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createWebsiteVersion(projectId: string, data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/projects/${projectId}/versions`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getWebsiteVersion(versionId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/versions/${versionId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // Project Assets
  static async getProjectAssets(projectId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/projects/${projectId}/assets`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createProjectAsset(projectId: string, data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/projects/${projectId}/assets`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // Sellers endpointy
  static async getSellersList() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/sellers`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }
}

export default ApiClient;