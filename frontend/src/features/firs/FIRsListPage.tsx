import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchFIRs } from '../../api/crimes'
import { Card, CardContent } from '@/components/ui/card'
import { usePermissions } from '../../hooks/usePermissions'
import { Button } from '@/components/ui/button'

const statusColors: Record<string, string> = {
  UNDER_INVESTIGATION: 'bg-amber-100 text-amber-800',
  CLOSED: 'bg-green-100 text-green-800',
  REPORTED: 'bg-blue-100 text-blue-800',
}

export function FIRsListPage() {
  const { canWrite } = usePermissions()

  const { data: firs, isLoading, error } = useQuery({
    queryKey: ['firs'],
    queryFn: fetchFIRs,
  })

  if (isLoading) return <p className="text-slate-500">Loading FIRs...</p>
  if (error) return <p className="text-red-600">Failed to load FIRs.</p>

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">FIRs</h1>
        {canWrite && (
          <Link to="/firs/new">
            <Button>+ New FIR</Button>
          </Link>
        )}
      </div>

      <div className="space-y-3">
        {firs?.map((fir) => (
          <Link key={fir.id} to={`/firs/${fir.id}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{fir.fir_number}</div>
                    <div className="text-sm text-slate-600">{fir.summary}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {fir.police_station_name} · Incident {fir.incident_date} · Complainant {fir.complainant_name}
                    </div>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      statusColors[fir.status] ?? 'bg-slate-100 text-slate-800'
                    }`}
                  >
                    {fir.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {firs?.length === 0 && (
          <p className="text-slate-500">No FIRs found.</p>
        )}
      </div>
    </div>
  )
}