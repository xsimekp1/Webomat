/**
 * Format number as Czech currency
 */
export function formatCurrency(value: number | null | undefined, currency: string = 'CZK'): string {
  if (value === null || value === undefined) {
    return '0 Kč'
  }
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format date as Czech format (DD.MM.YYYY)
 */
export function formatDate(value: string | Date | null | undefined): string {
  if (!value) {
    return '-'
  }
  const date = typeof value === 'string' ? new Date(value) : value
  return date.toLocaleDateString('cs-CZ', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/**
 * Format datetime as Czech format (DD.MM.YYYY HH:mm)
 */
export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) {
    return '-'
  }
  const date = typeof value === 'string' ? new Date(value) : value
  return date.toLocaleString('cs-CZ', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
