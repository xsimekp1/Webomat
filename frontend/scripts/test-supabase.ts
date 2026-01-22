/**
 * Diagnostický skript pro ověření připojení k Supabase
 * Spustit: npx ts-node scripts/test-supabase.ts
 */

import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import * as path from 'path'

// Načti .env.local
dotenv.config({ path: path.join(__dirname, '..', '.env.local') })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

console.log('=== Supabase Diagnostika ===\n')

// 1. Kontrola env proměnných
console.log('1. Kontrola konfigurace:')
if (!supabaseUrl) {
  console.error('   ❌ NEXT_PUBLIC_SUPABASE_URL není nastavena!')
  process.exit(1)
}
console.log(`   ✅ SUPABASE_URL: ${supabaseUrl}`)

if (!supabaseKey) {
  console.error('   ❌ NEXT_PUBLIC_SUPABASE_ANON_KEY není nastavena!')
  process.exit(1)
}
console.log(`   ✅ SUPABASE_ANON_KEY: ${supabaseKey.substring(0, 20)}...`)

// 2. Vytvoření klienta
const supabase = createClient(supabaseUrl, supabaseKey)

async function runDiagnostics() {
  console.log('\n2. Test připojení k Supabase:')

  try {
    // Zkus základní query
    const { data, error } = await supabase
      .from('sellers')
      .select('count')
      .limit(1)

    if (error) {
      console.error(`   ❌ Chyba: ${error.message}`)
      console.error(`   Kód: ${error.code}`)
      console.error(`   Detail: ${error.details || 'N/A'}`)

      if (error.code === '42P01') {
        console.log('\n   💡 Tabulka "sellers" neexistuje. Je třeba ji vytvořit v Supabase.')
      }
      return
    }

    console.log('   ✅ Připojení k Supabase funguje!')

  } catch (err) {
    console.error(`   ❌ Neočekávaná chyba: ${err}`)
    return
  }

  // 3. Výpis existujících uživatelů
  console.log('\n3. Existující uživatelé v tabulce "sellers":')

  try {
    const { data: sellers, error } = await supabase
      .from('sellers')
      .select('id, first_name, last_name, email, role, is_active, created_at')
      .order('created_at', { ascending: false })

    if (error) {
      console.error(`   ❌ Chyba při čtení: ${error.message}`)
      return
    }

    if (!sellers || sellers.length === 0) {
      console.log('   ⚠️  Tabulka je prázdná - žádní uživatelé')
      return
    }

    console.log(`   Nalezeno ${sellers.length} uživatel(ů):\n`)

    sellers.forEach((seller, index) => {
      console.log(`   ${index + 1}. ${seller.first_name} ${seller.last_name}`)
      console.log(`      Email: ${seller.email}`)
      console.log(`      Role: ${seller.role}`)
      console.log(`      Aktivní: ${seller.is_active ? 'Ano' : 'Ne'}`)
      console.log(`      ID: ${seller.id}`)
      console.log('')
    })

  } catch (err) {
    console.error(`   ❌ Neočekávaná chyba: ${err}`)
  }
}

runDiagnostics()
  .then(() => {
    console.log('=== Diagnostika dokončena ===')
  })
  .catch(console.error)
