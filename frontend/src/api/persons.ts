import { apiFetch } from './client'

export interface Phone {
  id: string
  person: string
  phone_number: string
  phone_type: string
  is_primary: boolean
  created_at: string
}

export interface Email {
  id: string
  person: string
  email: string
  email_type: string
  is_primary: boolean
  created_at: string
}

export interface Address {
  id: string
  person: string
  address_line: string
  city: string
  district: string
  state: string
  pincode: string
  address_type: string
  is_primary: boolean
  created_at: string
}

export interface Person {
  id: string
  first_name: string
  last_name: string
  date_of_birth: string | null
  gender: string
  nationality: string
  aadhaar_number: string | null
  father_or_guardian_name: string
  occupation: string
  notes: string
  phones: Phone[]
  emails: Email[]
  addresses: Address[]
  created_at: string
  updated_at: string
}

export interface PersonCaseRole {
  id: string
  person: string
  person_name: string
  case: string
  case_number: string
  role: string
  added_by: string
  added_by_name: string
  remarks: string
  added_at: string
}

export async function fetchPersons(): Promise<Person[]> {
  const res = await apiFetch('/api/persons/')
  if (!res.ok) throw new Error('Failed to fetch persons')
  return res.json()
}

export async function fetchPersonById(id: string): Promise<Person> {
  const res = await apiFetch(`/api/persons/${id}/`)
  if (!res.ok) throw new Error('Failed to fetch person')
  return res.json()
}

export async function fetchPersonCaseRoles(): Promise<PersonCaseRole[]> {
  const res = await apiFetch('/api/person-case-roles/')
  if (!res.ok) throw new Error('Failed to fetch person case roles')
  return res.json()
}