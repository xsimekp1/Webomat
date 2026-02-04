/**
 * Navigation utilities for CRM and dashboard navigation
 */

/**
 * Determines the correct back URL when navigating from project detail
 * @param businessId - Current project's business ID
 * @returns The correct navigation URL
 */
export const getBackUrl = (businessId: string): string => {
  if (typeof window !== 'undefined') {
    const lastCrmPage = localStorage.getItem('lastCrmPage')
    
    // Debug logování
    if (process.env.NODE_ENV === 'development') {
      console.log('getBackUrl - lastCrmPage:', lastCrmPage)
      console.log('getBackUrl - businessId:', businessId)
    }
    
    if (lastCrmPage) {
      // Přidat prefix pokud chybí a normalizovat URL
      let normalizedUrl = lastCrmPage.startsWith('/') ? lastCrmPage : `/${lastCrmPage}`
      let fullUrl = normalizedUrl.includes('/dashboard') ? normalizedUrl : `/dashboard${normalizedUrl}`
      
      if (process.env.NODE_ENV === 'development') {
        console.log('getBackUrl - normalizedUrl:', normalizedUrl)
        console.log('getBackUrl - fullUrl:', fullUrl)
      }
      
      // Pokud URL obsahuje business ID tohoto projektu, vrať ji
      if (fullUrl.includes(`/crm/${businessId}`)) {
        console.log('getBackUrl - returning specific CRM page:', fullUrl)
        return fullUrl
      }
      
      // Pokud obsahuje jiné business ID, vrať obecnou CRM stránku
      if (fullUrl.includes('/crm/')) {
        console.log('getBackUrl - returning generic CRM page')
        return '/dashboard/crm'
      }
    }
  }
  console.log('getBackUrl - returning default dashboard')
  return '/dashboard' // Safe fallback
}

/**
 * Stores the current CRM page for navigation back from project detail
 * @param businessId - Current business ID
 */
export const storeCrmPage = (businessId: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('lastCrmPage', `/dashboard/crm/${businessId}`)
  }
}

/**
 * Clears stored CRM navigation history
 */
export const clearCrmHistory = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('lastCrmPage')
  }
}