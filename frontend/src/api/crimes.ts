import { apiFetch } from './client'

export interface Crime {
  id: string
  category: string
  category_name: string
  police_station: string
  police_station_name: string
  reported_by: string
  reported_by_name: string
  description: string
  date_of_occurrence: string
  time_of_occurrence: string | null
  location_description: string
  latitude: number | null
  longitude: number | null
  status: string
  created_at: string
  updated_at: string
}

export interface FIR {
  id: string
  fir_number: string
  police_station: string
  police_station_name: string
  registered_by: string
  registered_by_name: string
  complainant_name: string
  complainant_phone: string
  date_filed: string
  incident_date: string
  incident_location: string
  status: string
  summary: string
  updated_at: string
}

export interface FIRCrime {
  id: string
  fir: string
  fir_number: string
  crime: string
  crime_category_name: string
  is_primary_offense: boolean
  created_at: string
}

export interface CrimeCategory {
  id: string
  name: string
}

export interface CreateCrimeInput {
  category: string
  police_station: string
  description: string
  date_of_occurrence: string
  time_of_occurrence?: string | null
  location_description?: string
  status?: string
}

export interface CreateFIRInput {
  fir_number: string
  police_station: string
  registered_by: string
  complainant_name: string
  complainant_phone?: string
  incident_date: string
  incident_location: string
  summary: string
  status?: string
}

export async function fetchCrimes(): Promise<Crime[]> {
  const res = await apiFetch('/api/crimes/')
  if (!res.ok) throw new Error('Failed to fetch crimes')
  return res.json()
}

export async function fetchFIRs(): Promise<FIR[]> {
  const res = await apiFetch('/api/firs/')
  if (!res.ok) throw new Error('Failed to fetch FIRs')
  return res.json()
}

export async function fetchCrimeById(id: string): Promise<Crime> {
  const res = await apiFetch(`/api/crimes/${id}/`)
  if (!res.ok) throw new Error('Failed to fetch crime')
  return res.json()
}

export async function fetchFIRById(id: string): Promise<FIR> {
  const res = await apiFetch(`/api/firs/${id}/`)
  if (!res.ok) throw new Error('Failed to fetch FIR')
  return res.json()
}

export async function fetchFIRCrimes(): Promise<FIRCrime[]> {
  const res = await apiFetch('/api/fir-crimes/')
  if (!res.ok) throw new Error('Failed to fetch FIR-crime links')
  return res.json()
}

export async function fetchCrimeCategories(): Promise<CrimeCategory[]> {
  const res = await apiFetch('/api/crime-categories/')
  if (!res.ok) throw new Error('Failed to fetch crime categories')
  return res.json()
}

export async function createCrime(input: CreateCrimeInput): Promise<Crime> {
  const res = await apiFetch('/api/crimes/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function updateCrime(id: string, input: Partial<CreateCrimeInput>): Promise<Crime> {
  const res = await apiFetch(`/api/crimes/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function createFIR(input: CreateFIRInput): Promise<FIR> {
  const res = await apiFetch('/api/firs/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function updateFIR(id: string, input: Partial<CreateFIRInput>): Promise<FIR> {
  const res = await apiFetch(`/api/firs/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}