
const RAW_BASE = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_URL || ''
export const API_BASE = RAW_BASE.replace(/\/+$/, '')

export function apiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${cleanPath}`
}