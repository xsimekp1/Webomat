/**
 * Skript pro vytvoření uživatele Andy v tabulce sellers
 * Spustit: npx tsx scripts/create-andy.ts
 */

import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import * as path from 'path'

dotenv.config({ path: path.join(__dirname, '..', '.env.local') })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Chybí SUPABASE_URL nebo SUPABASE_ANON_KEY v .env.local')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseKey)

async function createAndy() {
  console.log('=== Vytvoření uživatele Andy ===\n')

  // Nejprve zkontroluj, zda existují potřebné sloupce
  const { error: checkError } = await supabase
    .from('sellers')
    .select('password_hash, role, is_active')
    .limit(1)

  if (checkError && checkError.message.includes('does not exist')) {
    console.log('❌ Tabulka sellers nemá potřebné sloupce pro autentizaci!')
    console.log('\n📋 Spusť tento SQL v Supabase SQL Editoru:\n')
    console.log(`
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'sales' CHECK (role IN ('admin', 'sales'));
ALTER TABLE sellers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
    `)
    return
  }

  // Zkontroluj, zda Andy už existuje
  const { data: existing, error: existError } = await supabase
    .from('sellers')
    .select('id, first_name, last_name, email')
    .or('first_name.ilike.Andy,email.ilike.andy@webomat.cz')
    .limit(1)

  if (existError) {
    console.error(`❌ Chyba při kontrole: ${existError.message}`)
    return
  }

  if (existing && existing.length > 0) {
    console.log(`⚠️  Uživatel Andy už existuje:`)
    console.log(`   ID: ${existing[0].id}`)
    console.log(`   Jméno: ${existing[0].first_name} ${existing[0].last_name}`)
    console.log(`   Email: ${existing[0].email}`)

    // Aktualizuj heslo a roli
    console.log('\n🔄 Aktualizuji heslo a roli...')
    const { error: updateError } = await supabase
      .from('sellers')
      .update({
        password_hash: 'andy',
        role: 'admin',
        is_active: true
      })
      .eq('id', existing[0].id)

    if (updateError) {
      console.error(`❌ Chyba při aktualizaci: ${updateError.message}`)
      if (updateError.message.includes('does not exist')) {
        console.log('\n💡 Sloupce password_hash/role/is_active neexistují!')
        console.log('   Spusť SQL příkazy uvedené výše.')
      }
    } else {
      console.log('✅ Heslo a role aktualizovány!')
      console.log('\n🔐 Přihlašovací údaje:')
      console.log('   Username: Andy')
      console.log('   Password: andy')
    }
    return
  }

  // Vytvoř nového uživatele
  const newSeller = {
    seller_code: 'ANDY',
    first_name: 'Andy',
    last_name: 'Admin',
    email: 'andy@webomat.cz',
    password_hash: 'andy',
    role: 'admin',
    is_active: true,
    phone: '',
    notes: 'Testovací admin účet'
  }

  console.log('Vytvářím uživatele:')
  console.log(`   Jméno: ${newSeller.first_name} ${newSeller.last_name}`)
  console.log(`   Email: ${newSeller.email}`)
  console.log(`   Password: ${newSeller.password_hash}`)
  console.log(`   Role: ${newSeller.role}`)
  console.log('')

  const { data, error } = await supabase
    .from('sellers')
    .insert(newSeller)
    .select()

  if (error) {
    console.error(`❌ Chyba při vytváření: ${error.message}`)
    if (error.message.includes('does not exist')) {
      console.log('\n💡 Některé sloupce neexistují. Spusť SQL příkazy uvedené výše.')
    }
    return
  }

  if (data && data.length > 0) {
    console.log('✅ Uživatel Andy vytvořen!')
    console.log(`   ID: ${data[0].id}`)
    console.log('\n🔐 Přihlašovací údaje:')
    console.log('   Username: Andy')
    console.log('   Password: andy')
  }
}

createAndy()
  .then(() => {
    console.log('\n=== Hotovo ===')
  })
  .catch(console.error)
