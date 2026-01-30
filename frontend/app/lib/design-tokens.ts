/**
 * Design Tokens
 *
 * Centralized design system values for consistent styling across the app.
 */

export const colors = {
  primary: {
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    solid: '#667eea',
    light: '#e0e7ff',
    dark: '#4f46e5',
  },
  success: {
    solid: '#10b981',
    light: '#d1fae5',
    dark: '#065f46',
  },
  warning: {
    solid: '#f59e0b',
    light: '#fef3c7',
    dark: '#92400e',
  },
  danger: {
    solid: '#ef4444',
    light: '#fee2e2',
    dark: '#991b1b',
  },
  info: {
    solid: '#3b82f6',
    light: '#dbeafe',
    dark: '#1e40af',
  },
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
}

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
}

export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
}

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  glow: '0 4px 12px rgba(102, 126, 234, 0.4)',
}

export const typography = {
  fontFamily: {
    sans: 'Inter, system-ui, -apple-system, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
  },
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
}

export const transitions = {
  fast: '150ms ease',
  default: '200ms ease',
  slow: '300ms ease',
}

// Status colors mapping
export const statusColors = {
  // CRM statuses
  new: { bg: colors.info.light, text: colors.info.dark },
  calling: { bg: colors.warning.light, text: colors.warning.dark },
  interested: { bg: '#fef3c7', text: '#92400e' },
  offer_sent: { bg: '#e0e7ff', text: '#3730a3' },
  won: { bg: colors.success.light, text: colors.success.dark },
  lost: { bg: colors.danger.light, text: colors.danger.dark },
  dnc: { bg: colors.gray[100], text: colors.gray[700] },

  // Project statuses
  offer: { bg: colors.warning.light, text: colors.warning.dark },
  in_production: { bg: colors.info.light, text: colors.info.dark },
  delivered: { bg: '#e0e7ff', text: '#3730a3' },
  live: { bg: colors.success.light, text: colors.success.dark },
  cancelled: { bg: colors.danger.light, text: colors.danger.dark },

  // Deployment statuses
  none: { bg: colors.gray[100], text: colors.gray[600] },
  deploying: { bg: colors.warning.light, text: colors.warning.dark },
  deployed: { bg: colors.success.light, text: colors.success.dark },
  failed: { bg: colors.danger.light, text: colors.danger.dark },
  unpublished: { bg: colors.gray[100], text: colors.gray[600] },
}
