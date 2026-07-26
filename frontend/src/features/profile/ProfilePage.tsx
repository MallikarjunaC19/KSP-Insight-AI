import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '../../hooks/useAuth'
import { updateOfficer } from '../../api/accounts'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function ProfilePage() {
  const officer = useAuth((s) => s.officer)
  const setAuth = useAuth((s) => s.setAuth)
  const accessToken = useAuth((s) => s.accessToken)
  const [editing, setEditing] = useState(false)
  const [phone, setPhone] = useState(officer?.phone ?? '')
  const [email, setEmail] = useState(officer?.email ?? '')

  const mutation = useMutation({
    mutationFn: () => updateOfficer(officer!.id, { phone, email }),
    onSuccess: (updated) => {
      setAuth(accessToken!, { ...officer!, ...updated })
      setEditing(false)
    },
  })

  if (!officer) return null

  return (
    <div className="max-w-lg">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">My Profile</h1>
        {!editing && (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>Edit</Button>
        )}
      </div>
      <Card>
        <CardContent className="p-6 space-y-3 text-sm">
          <div className="flex justify-between"><span className="text-slate-400">Name</span><span className="font-medium">{officer.first_name} {officer.last_name}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Badge Number</span><span>{officer.badge_number}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Rank</span><span>{officer.rank_name}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Role</span><span>{officer.role_name}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Station</span><span>{officer.police_station_name}</span></div>
          {officer.jurisdiction_district && (
            <div className="flex justify-between"><span className="text-slate-400">District</span><span>{officer.jurisdiction_district}</span></div>
          )}

          {editing ? (
            <>
              <div>
                <Label>Phone</Label>
                <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div>
                <Label>Email</Label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              {mutation.isError && <p className="text-red-600">Failed to save: {(mutation.error as Error).message}</p>}
              <div className="flex gap-2 pt-2">
                <Button size="sm" disabled={mutation.isPending} onClick={() => mutation.mutate()}>
                  {mutation.isPending ? 'Saving...' : 'Save'}
                </Button>
                <Button size="sm" variant="outline" onClick={() => { setEditing(false); setPhone(officer.phone); setEmail(officer.email) }}>
                  Cancel
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="flex justify-between"><span className="text-slate-400">Phone</span><span>{officer.phone}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Email</span><span>{officer.email}</span></div>
            </>
          )}

          <div className="flex justify-between"><span className="text-slate-400">Joined</span><span>{officer.date_of_joining}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Username</span><span>{officer.username}</span></div>
        </CardContent>
      </Card>
    </div>
  )
}