// Shared types for Webomat
export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'sales'
  is_active: boolean
  phone?: string
  must_change_password: boolean
}

export interface Seller {
  id: string
  name: string
  email: string
  role: 'admin' | 'sales'
  is_active: boolean
}

export interface Business {
  id: string
  name: string
  address: string | null
  phone: string | null
  email: string | null
  website: string | null
  category: string | null
  notes: string | null
  status_crm: string
  owner_seller_id: string | null
  owner_seller_name: string | null
  next_follow_up_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface Activity {
  id: string
  business_id: string
  seller_id: string
  seller_name: string | null
  activity_type: string
  description: string
  outcome: string | null
  duration_minutes: number | null
  created_at: string | null
}

export interface Project {
  id: string
  business_id: string
  package: string
  status: string
  price_setup: number | null
  price_monthly: number | null
  domain: string | null
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CRMStats {
  total_leads: number
  new_leads: number
  calling: number
  interested: number
  offer_sent: number
  won: number
  lost: number
  dnc: number
  follow_ups_today: number
}

export interface TodayTask {
  id: string
  business_id: string
  business_name: string
  phone: string | null
  status_crm: string
  next_follow_up_at: string | null
  last_activity: string | null
}

export interface SellerDashboard {
  available_balance: number
  pending_projects_amount: number
  recent_invoices: any[]
  weekly_rewards: any[]
}