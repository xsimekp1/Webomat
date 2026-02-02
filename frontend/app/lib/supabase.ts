import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export interface Seller {
  id: string
  first_name: string
  last_name: string
  email: string
  password_hash?: string
  role: 'admin' | 'sales'
  is_active: boolean
  phone?: string
  notes?: string
  status?: string
  created_at: string
  updated_at?: string
}

// User type is now exported from context/AuthContext.tsx
// This file only exports the Supabase client and Seller interface
