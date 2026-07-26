import { useAuth } from './useAuth'

export function usePermissions() {
  const officer = useAuth((s) => s.officer)
  const role = officer?.role_name ?? ''

  return {
    isStateScoped: role === 'DGP' || role === 'SCRB Analyst',
    isDistrictScoped: role === 'SP / DIG',
    isStationScoped: role === 'Constable' || role === 'Station Officer',
    canWrite: role !== 'Constable' && role !== 'SCRB Analyst',
  }
}