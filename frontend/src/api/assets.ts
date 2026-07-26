import { apiFetch } from './client'

export interface VehicleOwnership {
  id: string
  vehicle: string
  owner: string
  owner_name: string
  ownership_type: string
  start_date: string
  end_date: string | null
  created_at: string
}

export interface Vehicle {
  id: string
  registration_number: string
  vehicle_type: string
  make: string
  model: string
  color: string
  chassis_number: string
  engine_number: string
  is_stolen: boolean
  status: string
  ownerships: VehicleOwnership[]
  created_at: string
  updated_at: string
}

export interface Property {
  id: string
  property_type: string
  description: string
  estimated_value: string
  owner: string | null
  owner_name: string | null
  case: string | null
  case_number: string | null
  status: string
  location: string
  created_at: string
  updated_at: string
}

export interface Weapon {
  id: string
  weapon_type: string
  license_number: string
  serial_number: string
  owner: string | null
  owner_name: string | null
  case: string | null
  case_number: string | null
  status: string
  description: string
  created_at: string
  updated_at: string
}

export async function fetchVehicles(): Promise<Vehicle[]> {
  const res = await apiFetch('/api/vehicles/')
  if (!res.ok) throw new Error('Failed to fetch vehicles')
  return res.json()
}

export async function fetchProperties(): Promise<Property[]> {
  const res = await apiFetch('/api/properties/')
  if (!res.ok) throw new Error('Failed to fetch properties')
  return res.json()
}

export async function fetchWeapons(): Promise<Weapon[]> {
  const res = await apiFetch('/api/weapons/')
  if (!res.ok) throw new Error('Failed to fetch weapons')
  return res.json()
}