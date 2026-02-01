/**
 * Skript pro seedování testovacích dat do databáze
 * Spustit: npx tsx scripts/seed-test-data.ts
 */

import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
import * as path from 'path'

// Načti frontend .env.local
dotenv.config({ path: path.join(__dirname, '..', '.env.local') })
// Načti backend .env jako fallback
dotenv.config({ path: path.join(__dirname, '..', '..', 'backend', '.env') })

// Zkus frontend proměnné, pak backend jako fallback
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Chybí SUPABASE_URL nebo SUPABASE_KEY')
  console.error('   Nastavte NEXT_PUBLIC_SUPABASE_URL/ANON_KEY v frontend/.env.local')
  console.error('   nebo SUPABASE_URL/SERVICE_ROLE_KEY v backend/.env')
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

    // 0. Cleanup - smaž staré testovací data
    console.log('🧹 Mažu staré testovací data...')

    // Smaž staré aktivity pro Andyho firmy
    await supabase.from('crm_activities').delete().eq('seller_id', andyId)

    // Smaž staré vydané faktury s TEST prefixem
    await supabase.from('invoices_issued').delete().like('invoice_number', 'TEST-%')

    // Smaž staré přijaté faktury s FP prefixem
    await supabase.from('invoices_received').delete().like('invoice_number', 'FP-%')

    // Smaž staré ledger entries
    await supabase.from('ledger_entries').delete().eq('seller_id', andyId)

    // Najdi a smaž projekty + firmy Andyho
    const { data: oldBusinesses } = await supabase
      .from('businesses')
      .select('id')
      .eq('owner_seller_id', andyId)

    if (oldBusinesses && oldBusinesses.length > 0) {
      const oldBusinessIds = oldBusinesses.map(b => b.id)
      await supabase.from('website_projects').delete().in('business_id', oldBusinessIds)
      await supabase.from('businesses').delete().in('id', oldBusinessIds)
    }

    console.log('✅ Staré data smazány')

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
      },
      {
        business_id: insertedBusinesses?.[1]?.id,
        seller_id: andyId,
        package: 'start',
        status: 'in_production',
      },
    ]

    const { data: insertedProjects, error: projectError } = await supabase
      .from('website_projects')
      .insert(projects)
      .select()

    if (projectError) throw projectError

    console.log(`✅ Vytvořeno ${insertedProjects?.length || 0} projektů`)

    // 3. Vytvoř testovací komise (ledger entries)
    // Expected balance: 5000 + 3000 + 500 + 1000 - 2000 = 7500 Kč
    console.log('💰 Vytvářím testovací ledger entries...')
    const commissions = [
      {
        seller_id: andyId,
        entry_type: 'commission_earned',
        amount: 5000,
        description: 'Provize za Veterinární kliniku - setup',
        related_business_id: insertedBusinesses?.[0]?.id,
        related_project_id: insertedProjects?.[0]?.id,
        is_test: true,
      },
      {
        seller_id: andyId,
        entry_type: 'commission_earned',
        amount: 3000,
        description: 'Provize za Kadeřnictví Elegant - setup',
        related_business_id: insertedBusinesses?.[1]?.id,
        related_project_id: insertedProjects?.[1]?.id,
        is_test: true,
      },
      {
        seller_id: andyId,
        entry_type: 'commission_earned',
        amount: 500,
        description: 'Provize za měsíční provoz webu',
        related_business_id: insertedBusinesses?.[0]?.id,
        is_test: true,
      },
      {
        seller_id: andyId,
        entry_type: 'admin_adjustment',
        amount: 1000,
        description: 'Bonus za výkon Q4 2024',
        notes: 'Mimořádná odměna za překročení cílů',
        is_test: true,
      },
      {
        seller_id: andyId,
        entry_type: 'payout_paid',
        amount: -2000,
        description: 'Vyplaceno na účet - leden 2025',
        notes: 'VS: 20250101',
        is_test: true,
      },
    ]
    // Note: Expected balance = 5000 + 3000 + 500 + 1000 - 2000 = 7500 Kč

    const { data: insertedCommissions, error: commissionError } = await supabase
      .from('ledger_entries')
      .insert(commissions)
      .select()

    if (commissionError) throw commissionError

    console.log(`✅ Vytvořeno ${insertedCommissions?.length || 0} ledger záznamů`)
    console.log(`   📊 Očekávaný zůstatek: 7500 Kč (5000 + 3000 + 500 + 1000 - 2000)`)

    // 4. Vytvoř testovací faktury
    console.log('📄 Vytvářím testovací faktury...')
    const invoices = [
      {
        seller_id: andyId,
        invoice_type: 'commission',
        invoice_number: 'FP-2024-001',
        issue_date: '2024-03-15',
        due_date: '2024-03-30',
        amount_total: 8000,
        status: 'paid',
        is_test: true,
      },
      {
        seller_id: andyId,
        invoice_type: 'commission',
        invoice_number: 'FP-2024-002',
        issue_date: '2024-04-01',
        due_date: '2024-04-15',
        amount_total: 5000,
        status: 'approved',
        is_test: true,
      },
    ]

    const { data: insertedInvoices, error: invoiceError } = await supabase
      .from('invoices_received')
      .insert(invoices)
      .select()

    if (invoiceError) throw invoiceError

    console.log(`✅ Vytvořeno ${insertedInvoices?.length || 0} faktur (invoices_received)`)

    // 5. Vytvoř testovací faktury vydané klientům (invoices_issued)
    console.log('📄 Vytvářím testovací faktury pro klienty (invoices_issued)...')

    // Pomocné funkce pro dynamické datumy
    const today = new Date()
    const formatDate = (date: Date) => date.toISOString().split('T')[0]
    const addDays = (date: Date, days: number) => {
      const result = new Date(date)
      result.setDate(result.getDate() + days)
      return result
    }

    // Nejdříve smaž staré testovací faktury
    const { error: deleteError } = await supabase
      .from('invoices_issued')
      .delete()
      .like('invoice_number', 'TEST-%')

    if (deleteError) {
      console.warn('⚠️ Varování při mazání starých faktur:', deleteError.message)
    }

    const invoicesIssued = [
      {
        // Faktura PO splatnosti - 15 dní
        business_id: insertedBusinesses?.[0]?.id,
        project_id: insertedProjects?.[0]?.id,
        seller_id: andyId,
        invoice_number: 'TEST-2025-0001',
        issue_date: formatDate(addDays(today, -30)),
        due_date: formatDate(addDays(today, -15)),  // 15 dní po splatnosti
        amount_without_vat: 12396,
        vat_rate: 21,
        vat_amount: 2604,
        amount_total: 15000,
        currency: 'CZK',
        payment_type: 'setup',
        status: 'overdue',
        description: 'Zřízení webu - balíček Premium',
      },
      {
        // Faktura PO splatnosti - 3 dny
        business_id: insertedBusinesses?.[1]?.id,
        project_id: insertedProjects?.[1]?.id,
        seller_id: andyId,
        invoice_number: 'TEST-2025-0002',
        issue_date: formatDate(addDays(today, -17)),
        due_date: formatDate(addDays(today, -3)),  // 3 dny po splatnosti
        amount_without_vat: 4132,
        vat_rate: 21,
        vat_amount: 868,
        amount_total: 5000,
        currency: 'CZK',
        payment_type: 'setup',
        status: 'overdue',
        description: 'Zřízení webu - balíček Start',
      },
      {
        // Faktura PŘED splatností - za 5 dní
        business_id: insertedBusinesses?.[0]?.id,
        project_id: insertedProjects?.[0]?.id,
        seller_id: andyId,
        invoice_number: 'TEST-2025-0003',
        issue_date: formatDate(addDays(today, -9)),
        due_date: formatDate(addDays(today, 5)),  // splatnost za 5 dní
        amount_without_vat: 826,
        vat_rate: 21,
        vat_amount: 174,
        amount_total: 1000,
        currency: 'CZK',
        payment_type: 'monthly',
        status: 'issued',
        description: 'Měsíční provoz webu - leden 2025',
      },
      {
        // Faktura PŘED splatností - za 20 dní
        business_id: insertedBusinesses?.[1]?.id,
        project_id: insertedProjects?.[1]?.id,
        seller_id: andyId,
        invoice_number: 'TEST-2025-0004',
        issue_date: formatDate(addDays(today, -2)),
        due_date: formatDate(addDays(today, 20)),  // splatnost za 20 dní
        amount_without_vat: 413,
        vat_rate: 21,
        vat_amount: 87,
        amount_total: 500,
        currency: 'CZK',
        payment_type: 'monthly',
        status: 'issued',
        description: 'Měsíční provoz webu - únor 2025',
      },
    ]

    const { data: insertedInvoicesIssued, error: invoiceIssuedError } = await supabase
      .from('invoices_issued')
      .insert(invoicesIssued)
      .select()

    if (invoiceIssuedError) throw invoiceIssuedError

    console.log(`✅ Vytvořeno ${insertedInvoicesIssued?.length || 0} faktur pro klienty (invoices_issued)`)

    // 6. Vytvoř testovací aktivity
    console.log('📝 Vytvářím testovací aktivity...')
    const activities = [
      {
        business_id: insertedBusinesses?.[0]?.id,
        seller_id: andyId,
        type: 'call',
        content: 'První kontakt - zájem o web',
        outcome: 'Zájem projeven',
        occurred_at: formatDate(addDays(today, -7)),
      },
      {
        business_id: insertedBusinesses?.[1]?.id,
        seller_id: andyId,
        type: 'email',
        content: 'Odeslána nabídka na webové stránky',
        outcome: 'Čeká na odpověď',
        occurred_at: formatDate(addDays(today, -3)),
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
    console.log(`   Ledger entries: ${insertedCommissions?.length || 0}`)
    console.log(`   Faktury přijaté (invoices_received): ${insertedInvoices?.length || 0}`)
    console.log(`   Faktury vydané (invoices_issued): ${insertedInvoicesIssued?.length || 0}`)
    console.log(`   Aktivity: ${insertedActivities?.length || 0}`)
    console.log('\n💰 Očekávaný zůstatek "K vyplacení": 7500 Kč')

  } catch (error) {
    console.error('❌ Chyba při seedování:', error)
    process.exit(1)
  }
}

seedTestData()
  .then(() => console.log('\n=== Hotovo ==='))
  .catch(console.error)