/**
 * Skript pro seedování testovacích dat do databáze
 * Spustit: npx tsx scripts/seed-test-data.ts
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

async function seedTestData() {
  console.log('=== Seedování testovacích dat ===\n')

  try {
    // Najdi Andyho ID
    const { data: andyData, error: andyError } = await supabase
      .from('sellers')
      .select('id')
      .eq('email', 'andy@webomat.cz')
      .limit(1)
      .single()

    if (andyError || !andyData) {
      console.error('❌ Andy uživatel nenalezen! Spusť nejdřív create-andy.ts')
      return
    }

    const andyId = andyData.id
    console.log(`👤 Používám Andyho ID: ${andyId}`)

    // 1. Vytvoř testovací firmy
    console.log('🏢 Vytvářím testovací firmy...')
    const businesses = [
      {
        name: 'Veterinární klinika Štěně',
        address_full: 'Praha 1, Staré Město',
        phone: '+420 123 456 789',
        email: 'info@veterina.cz',
        website: 'www.veterina.cz',
        status_crm: 'won',
        owner_seller_id: andyId,
      },
      {
        name: 'Kadeřnictví Elegant',
        address_full: 'Brno, centrum',
        phone: '+420 987 654 321',
        email: 'kontakt@kadernictvi.cz',
        status_crm: 'interested',
        owner_seller_id: andyId,
      },
      {
        name: 'Autoservis Rychlý',
        address_full: 'Praha 4, Pankrác',
        phone: '+420 555 123 456',
        status_crm: 'new',
        owner_seller_id: andyId,
      },
    ]

    const { data: insertedBusinesses, error: businessError } = await supabase
      .from('businesses')
      .insert(businesses)
      .select()

    if (businessError) throw businessError

    console.log(`✅ Vytvořeno ${insertedBusinesses?.length || 0} firem`)

    // 2. Vytvoř testovací projekty
    console.log('📋 Vytvářím testovací projekty...')
    const projects = [
      {
        business_id: insertedBusinesses?.[0]?.id,
        seller_id: andyId,
        package: 'premium',
        status: 'delivered',
        price_setup: 25000,
        price_monthly: 1500,
        domain: 'veterina.cz',
        notes: 'Kompletní web s rezervačním systémem',
      },
      {
        business_id: insertedBusinesses?.[1]?.id,
        seller_id: andyId,
        package: 'start',
        status: 'in_production',
        price_setup: 15000,
        domain: 'kadernictvi.cz',
        notes: 'Jednoduchý prezentační web',
      },
    ]

    const { data: insertedProjects, error: projectError } = await supabase
      .from('website_projects')
      .insert(projects)
      .select()

    if (projectError) throw projectError

    console.log(`✅ Vytvořeno ${insertedProjects?.length || 0} projektů`)

    // 3. Vytvoř testovací komise
    console.log('💰 Vytvářím testovací komise...')
    const commissions = [
      {
        seller_id: andyId,
        type: 'commission_earned',
        amount: 5000,
        related_invoice_id: null,
        notes: 'Provize za Veterinární kliniku',
      },
      {
        seller_id: andyId,
        type: 'commission_earned',
        amount: 3000,
        notes: 'Provize za Kadeřnictví Elegant',
      },
      {
        seller_id: andyId,
        type: 'payout_reserved',
        amount: -8000,
        notes: 'Vyplacení provizí',
      },
    ]

    const { data: insertedCommissions, error: commissionError } = await supabase
      .from('ledger_entries')
      .insert(commissions)
      .select()

    if (commissionError) throw commissionError

    console.log(`✅ Vytvořeno ${insertedCommissions?.length || 0} komisačních záznamů`)

    // 4. Vytvoř testovací faktury
    console.log('📄 Vytvářím testovací faktury...')
    const invoices = [
      {
        seller_id: andyId,
        invoice_number: '2024-001',
        issue_date: '2024-03-15',
        due_date: '2024-03-30',
        amount_total: 8000,
        status: 'paid',
        is_test: false,
      },
      {
        seller_id: andyId,
        invoice_number: '2024-002',
        issue_date: '2024-04-01',
        due_date: '2024-04-15',
        amount_total: 5000,
        status: 'approved',
        is_test: false,
      },
    ]

    const { data: insertedInvoices, error: invoiceError } = await supabase
      .from('invoices')
      .insert(invoices)
      .select()

    if (invoiceError) throw invoiceError

    console.log(`✅ Vytvořeno ${insertedInvoices?.length || 0} faktur`)

    // 5. Vytvoř testovací aktivity
    console.log('📝 Vytvářím testovací aktivity...')
    const activities = [
      {
        business_id: insertedBusinesses?.[0]?.id,
        seller_id: andyId,
        type: 'call',
        content: 'První kontakt - zájem o web',
        outcome: 'Zájem projeven',
      },
      {
        business_id: insertedBusinesses?.[1]?.id,
        seller_id: andyId,
        type: 'email',
        content: 'Odeslána nabídka na webové stránky',
        outcome: 'Čeká na odpověď',
      },
    ]

    const { data: insertedActivities, error: activityError } = await supabase
      .from('crm_activities')
      .insert(activities)
      .select()

    if (activityError) throw activityError

    console.log(`✅ Vytvořeno ${insertedActivities?.length || 0} aktivit`)

    console.log('\n🎉 Testovací data úspěšně seedována!')
    console.log('\n📊 Shrnutí:')
    console.log(`   Firmy: ${insertedBusinesses?.length || 0}`)
    console.log(`   Projekty: ${insertedProjects?.length || 0}`)
    console.log(`   Komise: ${insertedCommissions?.length || 0}`)
    console.log(`   Faktury: ${insertedInvoices?.length || 0}`)
    console.log(`   Aktivity: ${insertedActivities?.length || 0}`)

  } catch (error) {
    console.error('❌ Chyba při seedování:', error)
    process.exit(1)
  }
}

seedTestData()
  .then(() => console.log('\n=== Hotovo ==='))
  .catch(console.error)