import { useAuth } from '../hooks/useAuth'

const BASE_URL = import.meta.env.VITE_API_BASE_URL

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  // Mutex: if a refresh is already in flight, every other caller
  // awaits that same promise instead of firing its own request.
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/auth/token/refresh/`, {
        method: 'POST',
        credentials: 'include', // sends the httpOnly refresh cookie
      })
      if (!res.ok) return null
      const data = await res.json()
      return data.access as string
    } catch {
      return null
    } finally {
      // Clear after resolution so the *next* 401 (later in time) can refresh again.
    }
  })()

  const result = await refreshPromise
  refreshPromise = null
  return result
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = useAuth.getState().accessToken

  const doFetch = (accessToken: string | null) =>
    fetch(`${BASE_URL}${path}`, {
      ...options,
      credentials: 'include',
      headers: {
            ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
            ...options.headers,
          },
      })

  let res = await doFetch(token)

  if (res.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      useAuth.getState().setAuth(newToken, useAuth.getState().officer!)
      res = await doFetch(newToken)
    } else {
      useAuth.getState().clearAuth()
    }
  }

  return res
}