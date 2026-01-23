// Utility functions for deduplication and validation

import { supabase } from './supabase'

export interface ContactData {
  name: string
  ico?: string
  // other fields
}

export async function checkContactDuplicates(contact: ContactData): Promise<{
  isDuplicate: boolean
  warnings: string[]
}> {
  const warnings: string[] = []
  let isDuplicate = false

  // Check exact ICO match (hard duplicate)
  if (contact.ico) {
    const { data: icoMatch } = await supabase
      .from('contacts')
      .select('id, name')
      .eq('ico', contact.ico)
      .single()

    if (icoMatch) {
      isDuplicate = true
      warnings.push(`Kontakt s IČO ${contact.ico} už existuje: ${icoMatch.name}`)
    }
  }

  // Check similar name (warning)
  if (contact.name) {
    const { data: nameMatches } = await supabase
      .from('contacts')
      .select('id, name, city')
      .ilike('name', `%${contact.name}%`)
      .limit(5)

    if (nameMatches && nameMatches.length > 0) {
      warnings.push(`Podobné názvy nalezeny: ${nameMatches.map(m => m.name).join(', ')}`)
    }
  }

  return { isDuplicate, warnings }
}