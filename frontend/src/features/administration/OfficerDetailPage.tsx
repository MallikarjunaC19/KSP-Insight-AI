import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchOfficerById } from '../../api/accounts'
import { Card, CardContent } from '@/components/ui/card'

export function OfficerDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: officer, isLoading, error } = useQuery({
    queryKey: ['officer', id],
    queryFn: () => fetchOfficerById(id!),
    enabled: !!id,
  })

  if (isLoading) return <p className="text-slate-500">Loading officer...</p>
  if (error || !officer) return <p className="text-red-600">Failed to load officer.</p>

  return (
    <div className="max-w-lg">
      <Link to="/administration" className="text-sm text-blue-600 hover:underline">← Back to Administration</Link>
      <h1 className="text-2xl font-bold mt-2 mb-4">{officer.first_name} {officer.last_name}</h1>
      <Card>
        <CardContent className="p-6 space-y-3 text-sm">
          <div className="flex justify-between"><span className="text-slate-400">Badge Number</span><span className="font-medium">{officer.badge_number}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Rank</span><span>{officer.rank_name}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Role</span><span>{officer.role_name}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Station</span><span>{officer.police_station_name}</span></div>
          {officer.jurisdiction_district && (
            <div className="flex justify-between"><span className="text-slate-400">District</span><span>{officer.jurisdiction_district}</span></div>
          )}
          <div className="flex justify-between"><span className="text-slate-400">Phone</span><span>{officer.phone}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Email</span><span>{officer.email}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Joined</span><span>{officer.date_of_joining}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Username</span><span>{officer.username}</span></div>
          <div className="flex justify-between">
            <span className="text-slate-400">Status</span>
            <span className={officer.is_active ? 'text-green-600' : 'text-red-600'}>
              {officer.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}