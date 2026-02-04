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



  // ============================================
  // Web Project Management endpoints
  // ============================================

  static async getWebProject(projectId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/web-project/${projectId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async updateWebProject(projectId: string, data: any) {
    const response = await axios.put(
      `${API_BASE_URL}/web-project/${projectId}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getWebProjectVersions(projectId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/web-project/${projectId}/versions`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createWebProjectVersion(projectId: string, data: any) {
    const response = await axios.post(
      `${API_BASE_URL}/web-project/${projectId}/versions`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async updateWebProjectVersion(versionId: string, data: any) {
    const response = await axios.put(
      `${API_BASE_URL}/web-project/versions/${versionId}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async deployVersion(versionId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/web-project/versions/${versionId}/deploy`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async undeployVersion(versionId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/web-project/versions/${versionId}/undeploy`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async captureScreenshot(versionId: string) {
    const response = await axios.post(
      `${API_BASE_URL}/web-project/versions/${versionId}/screenshot`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async createShareLink(versionId: string, data?: { expires_in_days?: number; max_views?: number }) {
    const response = await axios.post(
      `${API_BASE_URL}/web-project/versions/${versionId}/share-link`,
      data || {},
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getVersionComments(versionId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/web-project/versions/${versionId}/comments`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async updateComment(commentId: string, data: { status?: string; resolution_note?: string }) {
    const response = await axios.put(
      `${API_BASE_URL}/web-project/comments/${commentId}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async markVersionAsCurrent(versionId: string) {
    const response = await axios.put(
      `${API_BASE_URL}/web-project/versions/${versionId}`,
      { is_current: true },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async deleteVersion(versionId: string) {
    const response = await axios.delete(
      `${API_BASE_URL}/web-project/versions/${versionId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async deleteProject(projectId: string) {
    const response = await axios.delete(
      `${API_BASE_URL}/web-project/${projectId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // ============================================
  // Public Preview endpoints (no auth)
  // ============================================

  static async getPreviewInfo(token: string) {
    const response = await axios.get(`${API_BASE_URL}/preview/${token}`);
    return response.data;
  }

  static async getPreviewHtml(token: string) {
    const response = await axios.get(`${API_BASE_URL}/preview/${token}/html`);
    return response.data;
  }

  static async addPreviewComment(token: string, data: {
    content: string;
    author_name?: string;
    author_email?: string;
    anchor_type?: string;
    anchor_x?: number;
    anchor_y?: number;
  }) {
    const response = await axios.post(
      `${API_BASE_URL}/preview/${token}/comments`,
      data,
      { headers: { 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getPreviewComments(token: string) {
    const response = await axios.get(`${API_BASE_URL}/preview/${token}/comments`);
    return response.data;
  }

  // ============================================
  // Platform Feedback endpoints
  // ============================================

  static async submitFeedback(data: {
    content: string;
    category?: 'bug' | 'idea' | 'ux' | 'other';
    priority?: 'low' | 'medium' | 'high';
    page_url?: string;
  }) {
    const response = await axios.post(
      `${API_BASE_URL}/feedback`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getMyFeedback() {
    const response = await axios.get(
      `${API_BASE_URL}/feedback`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async getAllFeedback(params?: { status?: string; category?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.category) queryParams.append('category', params.category);

    const url = `${API_BASE_URL}/admin/feedback${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await axios.get(url, { headers: ApiClient.getAuthHeaders() });
    return response.data;
  }

  static async updateFeedbackStatus(feedbackId: string, data: { status?: string; admin_note?: string }) {
    const response = await axios.put(
      `${API_BASE_URL}/admin/feedback/${feedbackId}`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // ============================================
  // Invoice Management endpoints
  // ============================================

  static async getProjectInvoices(projectId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/projects/${projectId}/invoices`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async generateProjectInvoice(projectId: string, data: {
    amount_without_vat: number;
    payment_type?: 'setup' | 'monthly' | 'other';
    description?: string;
    vat_rate?: number;
    due_days?: number;
  }) {
    const response = await axios.post(
      `${API_BASE_URL}/crm/projects/${projectId}/generate-invoice`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async updateInvoiceStatus(invoiceId: string, data: {
    status: 'draft' | 'issued' | 'paid' | 'overdue' | 'cancelled';
    paid_date?: string;
  }) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/status`,
      data,
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getInvoiceDetail(invoiceId: string) {
    const response = await axios.get(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // PDF Invoice Generation
  static async generateInvoicePdf(invoiceId: string): Promise<{ pdf_url: string; storage_path: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/generate-pdf`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async downloadInvoicePdf(invoiceId: string): Promise<string> {
    // Returns URL for redirect/download
    return `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/pdf`;
  }

  static async generateReceivedInvoicePdf(invoiceId: string): Promise<{ pdf_url: string; storage_path: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/crm/invoices-received/${invoiceId}/generate-pdf`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async downloadReceivedInvoicePdf(invoiceId: string): Promise<string> {
    return `${API_BASE_URL}/crm/invoices-received/${invoiceId}/pdf`;
  }

  static async updateBusinessStatus(businessId: string, status: string) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/businesses/${businessId}/status`,
      { status },
      {
        headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' }
      }
    );
    return response.data;
  }

  // ============================================
  // Invoice Approval Workflow endpoints
  // ============================================

  static async getAdminInvoices(params?: {
    status?: string;
    seller_id?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status_filter', params.status);
    if (params?.seller_id) queryParams.append('seller_id', params.seller_id);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());

    const url = `${API_BASE_URL}/crm/admin/invoices${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await axios.get(url, { headers: ApiClient.getAuthHeaders() });
    return response.data;
  }

  static async submitInvoiceForApproval(invoiceId: string) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/submit-for-approval`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async approveInvoice(invoiceId: string) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/approve`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async rejectInvoice(invoiceId: string, reason: string) {
    const response = await axios.put(
      `${API_BASE_URL}/crm/invoices-issued/${invoiceId}/reject`,
      { reason },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  static async getSellerClaims() {
    const response = await axios.get(
      `${API_BASE_URL}/crm/seller/claims`,
    { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  // ============================================
  // Admin endpoints
  // ============================================

  static async getUsers() {
    const response = await axios.get(
      `${API_BASE_URL}/admin/users`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async toggleUserActive(userId: string) {
    const response = await axios.put(
      `${API_BASE_URL}/admin/users/${userId}/toggle-active`,
      {},
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }

  static async resetUserPassword(userId: string, newPassword?: string) {
    const response = await axios.post(
      `${API_BASE_URL}/admin/users/${userId}/reset-password`,
      { new_password: newPassword },
      { headers: { ...ApiClient.getAuthHeaders(), 'Content-Type': 'application/json' } }
    );
    return response.data;
  }

  // ============================================
  // Seller Account Ledger endpoint
  // ============================================

  static async getSellerAccountLedger(params?: {
    range?: string;
    type?: string;
    status?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.range) queryParams.append('range', params.range);
    if (params?.type) queryParams.append('type', params.type);
    if (params?.status) queryParams.append('status', params.status);

    const response = await axios.get(
      `${API_BASE_URL}/crm/seller/account/ledger?${queryParams}`,
      { headers: ApiClient.getAuthHeaders() }
    );
    return response.data;
  }
}

export default ApiClient;