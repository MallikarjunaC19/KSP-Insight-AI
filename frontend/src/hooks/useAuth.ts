import { create } from 'zustand'

interface Officer {
  id: string
  username: string
  first_name: string
  last_name: string
  badge_number: string
  rank_name: string
  role_name: string
  police_station_name: string
  jurisdiction_district: string
  phone: string
  email: string
  date_of_joining: string
}

interface AuthState {
  accessToken: string | null
  officer: Officer | null
  setAuth: (token: string, officer: Officer) => void
  clearAuth: () => void
}

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  officer: null,
  setAuth: (accessToken, officer) => set({ accessToken, officer }),
  clearAuth: () => set({ accessToken: null, officer: null }),
}))