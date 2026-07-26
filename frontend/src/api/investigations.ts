import { apiFetch } from './client'

export interface InvestigationCase {
  id: string
  case_number: string
  fir: string
  fir_number: string
  lead_officer: string
  lead_officer_name: string
  status: string
  priority: string
  opened_date: string
  closed_date: string | null
  summary: string
  created_at: string
  updated_at: string
}

export interface Investigation {
  id: string
  case: string
  case_number: string
  officer: string
  officer_name: string
  start_date: string
  end_date: string | null
  findings: string
  status: string
  created_at: string
}

export interface InvestigationStep {
  id: string
  investigation: string
  case_number: string
  description: string
  performed_by: string
  performed_by_name: string
  step_date: string
  created_at: string
}

export interface Arrest {
  id: string
  case: string
  case_number: string
  arresting_officer: string
  arresting_officer_name: string
  arrested_person_name: string
  arrested_person_details: string
  arrest_date: string
  arrest_location: string
  remarks: string
  created_at: string
}

export interface Chargesheet {
  id: string
  case: string
  case_number: string
  filed_by: string
  filed_by_name: string
  court_referred: string
  filing_date: string
  sections_summary: string
  status: string
  created_at: string
  updated_at: string
}

export interface CourtCase {
  id: string
  chargesheet: string
  case_number: string
  court_case_number: string
  court_name: string
  filing_date: string
  status: string
  next_hearing_date: string | null
  verdict: string
  verdict_date: string | null
  created_at: string
  updated_at: string
}

export async function fetchInvestigationCases(): Promise<InvestigationCase[]> {
  const res = await apiFetch('/api/investigation-cases/')
  if (!res.ok) throw new Error('Failed to fetch investigation cases')
  return res.json()
}

export async function fetchInvestigationCaseById(id: string): Promise<InvestigationCase> {
  const res = await apiFetch(`/api/investigation-cases/${id}/`)
  if (!res.ok) throw new Error('Failed to fetch investigation case')
  return res.json()
}

export async function fetchInvestigations(): Promise<Investigation[]> {
  const res = await apiFetch('/api/investigations/')
  if (!res.ok) throw new Error('Failed to fetch investigations')
  return res.json()
}

export async function fetchInvestigationSteps(): Promise<InvestigationStep[]> {
  const res = await apiFetch('/api/investigation-steps/')
  if (!res.ok) throw new Error('Failed to fetch investigation steps')
  return res.json()
}

export async function fetchArrests(): Promise<Arrest[]> {
  const res = await apiFetch('/api/arrests/')
  if (!res.ok) throw new Error('Failed to fetch arrests')
  return res.json()
}

export async function fetchChargesheets(): Promise<Chargesheet[]> {
  const res = await apiFetch('/api/chargesheets/')
  if (!res.ok) throw new Error('Failed to fetch chargesheets')
  return res.json()
}

export async function fetchCourtCases(): Promise<CourtCase[]> {
  const res = await apiFetch('/api/court-cases/')
  if (!res.ok) throw new Error('Failed to fetch court cases')
  return res.json()
}

export interface CreateInvestigationCaseInput {
  case_number: string
  fir: string
  lead_officer: string
  status?: string
  priority?: string
  closed_date?: string | null
  summary?: string
}

export async function createInvestigationCase(input: CreateInvestigationCaseInput): Promise<InvestigationCase> {
  const res = await apiFetch('/api/investigation-cases/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export async function updateInvestigationCase(id: string, input: Partial<CreateInvestigationCaseInput>): Promise<InvestigationCase> {
  const res = await apiFetch(`/api/investigation-cases/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface CreateInvestigationInput {
  case: string
  officer: string
  end_date?: string | null
  findings?: string
  status?: string
}

export async function createInvestigation(input: CreateInvestigationInput): Promise<Investigation> {
  const res = await apiFetch('/api/investigations/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface CreateInvestigationStepInput {
  investigation: string
  description: string
  performed_by: string
  step_date: string
}

export async function createInvestigationStep(input: CreateInvestigationStepInput): Promise<InvestigationStep> {
  const res = await apiFetch('/api/investigation-steps/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface CreateArrestInput {
  case: string
  arresting_officer: string
  arrested_person_name: string
  arrested_person_details?: string
  arrest_date: string
  arrest_location?: string
  remarks?: string
}

export async function createArrest(input: CreateArrestInput): Promise<Arrest> {
  const res = await apiFetch('/api/arrests/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface CreateChargesheetInput {
  case: string
  filed_by: string
  court_referred?: string
  filing_date: string
  sections_summary: string
  status?: string
}

export async function createChargesheet(input: CreateChargesheetInput): Promise<Chargesheet> {
  const res = await apiFetch('/api/chargesheets/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}

export interface CreateCourtCaseInput {
  chargesheet: string
  court_case_number: string
  court_name?: string
  filing_date: string
  status?: string
  next_hearing_date?: string | null
  verdict?: string
  verdict_date?: string | null
}

export async function createCourtCase(input: CreateCourtCaseInput): Promise<CourtCase> {
  const res = await apiFetch('/api/court-cases/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(JSON.stringify(err))
  }
  return res.json()
}