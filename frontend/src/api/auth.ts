const BASE_URL = import.meta.env.VITE_API_BASE_URL

export interface LoginResponse {
  access: string
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/api/auth/token/`, {
    method: 'POST',
    credentials: 'include', // required to receive the refresh_token cookie
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    throw new Error('Invalid username or password')
  }
  return res.json()
}

export async function fetchMe(accessToken: string) {
  const res = await fetch(`${BASE_URL}/api/officers/me/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'ngrok-skip-browser-warning': 'true',
    },
  })
  if (!res.ok) throw new Error('Failed to fetch officer profile')
  return res.json()
}