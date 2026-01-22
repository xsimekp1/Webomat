import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import * as path from 'path'

dotenv.config({ path: path.join(__dirname, '..', '.env.local') })

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

async function checkSchema() {
  console.log('=== Kontrola struktury tabulky sellers ===\n')

  // Zkus všechny možné sloupce
  const possibleColumns = [
    'id', 'name', 'first_name', 'last_name', 'full_name',
    'email', 'username', 'login', 'password', 'password_hash',
    'role', 'user_role', 'type', 'is_active', 'active', 'status',
    'created_at', 'updated_at', 'phone', 'commission_percent',
    'commission', 'notes', 'avatar', 'avatar_url'
  ]

  const existingColumns: string[] = []

  console.log('Existující sloupce:')
  for (const col of possibleColumns) {
    const { error } = await supabase.from('sellers').select(col).limit(1)
    if (!error) {
      console.log(`  ✅ ${col}`)
      existingColumns.push(col)
    }
  }

  console.log('\nChybějící sloupce (potřebné pro auth):')
  const requiredForAuth = ['password_hash', 'role', 'is_active']
  for (const col of requiredForAuth) {
    if (!existingColumns.includes(col)) {
      console.log(`  ❌ ${col}`)
    }
  }

  console.log('\n📋 SQL pro přidání chybějících sloupců:')
  console.log(`
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'sales' CHECK (role IN ('admin', 'sales'));
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
  `)
}

checkSchema()
