import { apiFetch } from './client'

export interface PoliceStation {
  id: string
  name: string
}

export async function fetchPoliceStations(): Promise<PoliceStation[]> {
  const res = await apiFetch('/api/police-stations/')
  if (!res.ok) throw new Error('Failed to fetch police stations')
  return res.json()
}

export interface OfficerSummary {
  id: string
  first_name: string
  last_name: string
  badge_number: string
}

export interface OfficerSummary {
  id: string
  first_name: string
  last_name: string
  badge_number: string
}

export async function fetchOfficers(): Promise<OfficerSummary[]> {
  const res = await apiFetch('/api/officers/')
  if (!res.ok) throw new Error('Failed to fetch officers')
  return res.json()
}

export interface UpdateOfficerInput {
  phone?: string
  email?: string
}

export async function updateOfficer(id: string, input: UpdateOfficerInput) {
  const res = await apiFetch(`/api/officers/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface OfficerDetail {
  id: string
  username: string
  badge_number: string
  first_name: string
  last_name: string
  rank_name: string
  police_station_name: string
  role_name: string
  jurisdiction_district: string
  phone: string
  email: string
  date_of_joining: string
  is_active: boolean
}

export async function fetchOfficerById(id: string): Promise<OfficerDetail> {
  const res = await apiFetch(`/api/officers/${id}/`)
  if (!res.ok) throw new Error('Failed to fetch officer')
  return res.json()
}



