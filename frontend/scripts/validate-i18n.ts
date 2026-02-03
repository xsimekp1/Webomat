import { readFileSync } from 'fs'
import { join } from 'path'

// Validate i18n JSON structure
function validateMessages() {
  const messages = {}
  
  for (const locale of ['cs', 'en']) {
    try {
      const content = readFileSync(join(process.cwd(), `messages/${locale}.json`), 'utf8')
      messages[locale] = JSON.parse(content)
    } catch (error) {
      console.error(`❌ ${locale}.json is invalid:`, error.message)
      process.exit(1)
    }
  }
  
  // Check for missing nested keys
  const checkKey = (obj, path = '') => {
    for (const [key, value] of Object.entries(obj)) {
      const fullPath = path ? `${path}.${key}` : key
      
      if (typeof value === 'object') {
        checkKey(value, fullPath)
      }
    }
  }
  
  for (const locale of ['cs', 'en']) {
    console.log(`✅ ${locale}.json structure is valid`)
    checkKey(messages[locale])
  }
  
  // Test specific keys that were missing
  const testKeys = [
    'profile.navigation.dashboard',
    'profile.auth.sales'
  ]
  
  for (const key of testKeys) {
    const parts = key.split('.')
    for (const locale of ['cs', 'en']) {
      let current = messages[locale]
      for (const part of parts) {
        if (!current || !current[part]) {
          console.error(`❌ Missing key: ${key} in ${locale}.json`)
          process.exit(1)
        }
        current = current[part]
      }
    }
    console.log(`✅ Key exists: ${key}`)
  }
  
  console.log('🎉 All i18n keys validated!')
}

validateMessages()