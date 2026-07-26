import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchCrimes } from '../../api/crimes'
import { usePermissions } from '../../hooks/usePermissions'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const statusColors: Record<string, string> = {
  UNDER_INVESTIGATION: 'bg-amber-100 text-amber-800',
  CLOSED: 'bg-green-100 text-green-800',
  REPORTED: 'bg-blue-100 text-blue-800',
}

export function CrimesListPage() {
  const { canWrite } = usePermissions()

  const { data: crimes, isLoading, error } = useQuery({
    queryKey: ['crimes'],
    queryFn: fetchCrimes,
  })

  if (isLoading) return <p className="text-slate-500">Loading crimes...</p>
  if (error) return <p className="text-red-600">Failed to load crimes.</p>

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Crimes</h1>
        {canWrite && (
          <Link to="/crimes/new">
            <Button>+ New Crime</Button>
          </Link>
        )}
      </div>

      <div className="space-y-3">
        {crimes?.map((crime) => (
          <Link key={crime.id} to={`/crimes/${crime.id}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{crime.category_name}</div>
                    <div className="text-sm text-slate-600">{crime.description}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {crime.police_station_name} · {crime.date_of_occurrence} · Reported by {crime.reported_by_name}
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded ${statusColors[crime.status] ?? 'bg-slate-100 text-slate-800'}`}>
                    {crime.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {crimes?.length === 0 && <p className="text-slate-500">No crimes found.</p>}
      </div>
    </div>
  )
}
