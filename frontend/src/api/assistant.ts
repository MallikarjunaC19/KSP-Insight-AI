import { apiFetch } from './client'

export interface SqlTraceEntry {
  tool: string
  executed_sql: string
  row_count: number
}

export interface MlTraceEntry {
  tool: string
  model: string
  prediction: string
  confidence: number | string
  top_factors: { feature: string; value: unknown; impact: number; encoded: boolean }[]
  used_defaults: string[]
  prediction_history_id: string
}

export interface ChatMessageMetadata {
  tools_used?: string[]
  elapsed_ms?: number
  model?: string
  sql_trace?: SqlTraceEntry[]
  ml_trace?: MlTraceEntry[]
  audio_url?: string | null
}

export interface ChatMessage {
  id: string
  conversation: string
  sender: 'USER' | 'AI'
  content: string
  metadata: ChatMessageMetadata | null
  created_at: string
}

export interface Conversation {
  id: string
  officer: string
  case: string | null
  case_number: string | null
  title: string
  is_active: boolean
  messages: ChatMessage[]
  started_at: string
  updated_at: string
}

export async function fetchConversations(): Promise<Conversation[]> {
  const res = await apiFetch('/api/conversations/')
  if (!res.ok) throw new Error('Failed to fetch conversations')
  return res.json()
}

export async function createConversation(title: string): Promise<Conversation> {
  const res = await apiFetch('/api/conversations/', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function sendMessage(conversationId: string, message: string): Promise<ChatMessage> {
  const formData = new FormData()
  formData.append('message', message)
  const res = await apiFetch(`/api/conversations/${conversationId}/send-message/`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function exportConversationPdf(conversationId: string): Promise<{ download_url: string }> {
  const res = await apiFetch(`/api/conversations/${conversationId}/export-pdf/`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}
export async function sendAudioMessage(conversationId: string, audioBlob: Blob): Promise<ChatMessage & { transcribed_text?: string | null }> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  const res = await apiFetch(`/api/conversations/${conversationId}/send-message/`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

const API_BASE = import.meta.env.VITE_API_BASE_URL

export function resolveMediaUrl(url: string): string {
  if (url.startsWith('http')) return url
  return `${API_BASE}${url}`
}