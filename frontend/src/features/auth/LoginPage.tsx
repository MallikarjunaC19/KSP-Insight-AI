import { useState } from 'react'
import { login, fetchMe } from '../../api/auth'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import kspLogo from '../../assets/ksp-logo-banner.jpg'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const setAuth = useAuth((s) => s.setAuth)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access } = await login(username, password)
      const officer = await fetchMe(access)
      setAuth(access, officer)
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      if (message.toLowerCase().includes('failed to fetch') || message.toLowerCase().includes('network')) {
        setError('Cannot reach the server. Check your connection and try again.')
      } else {
        setError('Incorrect username or password.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
         <img src={kspLogo} alt="Karnataka State Police" className="h-16 mx-auto mb-4 bg-white rounded-lg px-4 py-2" />
         <h1 className="text-xl font-semibold text-white">KSP Insight AI</h1>
         <p className="text-sm text-slate-400 mt-1">Officer Portal</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder=""
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1"
              />
            </div>

            {error && (
              <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading || !username || !password}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Access is logged and restricted to authorized officers.
        </p>
      </div>
    </div>
  )
}