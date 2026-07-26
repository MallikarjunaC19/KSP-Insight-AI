import { apiFetch } from './client'

export type AuditActionType = 'QUERY' | 'LOGIN' | 'DATA_ACCESS' | 'EXPORT' | 'OTHER'

export interface AuditLogEntry {
  id: string
  officer: string // officer UUID
  officer_name: string
  action_type: AuditActionType
  description: string
  related_conversation: string | null // conversation UUID
  ip_address: string | null
  created_at: string // ISO timestamp, e.g. "2026-07-26T09:48:18.483490+05:30"
}

// Confirmed via live curl: no DEFAULT_PAGINATION_CLASS in REST_FRAMEWORK settings,
// so this endpoint returns a plain JSON array, not a {count, next, previous, results} envelope.
export async function fetchAuditLog(): Promise<AuditLogEntry[]> {
  const res = await apiFetch('/api/audit-logs/')
  if (!res.ok) throw new Error(`Failed to fetch audit log: ${res.status}`)
  return res.json()
}