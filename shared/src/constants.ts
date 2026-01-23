// Shared constants for Webomat
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const CRM_STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  new: { label: 'Nový', color: '#3b82f6', bg: '#dbeafe' },
  calling: { label: 'Voláno', color: '#eab308', bg: '#fef9c3' },
  interested: { label: 'Zájem', color: '#f97316', bg: '#ffedd5' },
  offer_sent: { label: 'Nabídka', color: '#8b5cf6', bg: '#ede9fe' },
  won: { label: 'Vyhráno', color: '#22c55e', bg: '#dcfce7' },
  lost: { label: 'Ztraceno', color: '#6b7280', bg: '#f3f4f6' },
  dnc: { label: 'DNC', color: '#ef4444', bg: '#fee2e2' },
}

export const ACTIVITY_ICONS: Record<string, string> = {
  call: '📞',
  email: '📧',
  meeting: '🤝',
  note: '📝',
  message: '💬',
}

export const PROJECT_STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  offer: { label: 'Nabídka', color: '#8b5cf6', bg: '#ede9fe' },
  won: { label: 'Vyhráno', color: '#22c55e', bg: '#dcfce7' },
  in_production: { label: 'Ve výrobě', color: '#f97316', bg: '#ffedd5' },
  delivered: { label: 'Dodáno', color: '#3b82f6', bg: '#dbeafe' },
  live: { label: 'Live', color: '#10b981', bg: '#d1fae5' },
  cancelled: { label: 'Zrušeno', color: '#6b7280', bg: '#f3f4f6' },
}

export const PACKAGE_CONFIG: Record<string, { label: string; color: string }> = {
  start: { label: 'Start', color: '#3b82f6' },
  profi: { label: 'Profi', color: '#8b5cf6' },
  premium: { label: 'Premium', color: '#f59e0b' },
  custom: { label: 'Custom', color: '#ec4899' },
}