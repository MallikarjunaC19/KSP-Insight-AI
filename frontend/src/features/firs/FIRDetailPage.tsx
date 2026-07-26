import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchFIRById, fetchFIRCrimes } from '../../api/crimes'
import { Card, CardContent } from '@/components/ui/card'
import { usePermissions } from '../../hooks/usePermissions'

export function FIRDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { canWrite } = usePermissions()

  const { data: fir, isLoading: firLoading, error: firError } = useQuery({
    queryKey: ['fir', id],
    queryFn: () => fetchFIRById(id!),
    enabled: !!id,
  })

  const { data: allLinks, isLoading: linksLoading } = useQuery({
    queryKey: ['fircrimes'],
    queryFn: fetchFIRCrimes,
  })

  if (firLoading || linksLoading) return <p className="text-slate-500">Loading FIR...</p>
  if (firError || !fir) return <p className="text-red-600">Failed to load FIR.</p>

  const linkedCrimes = allLinks?.filter((link) => link.fir === id) ?? []

  return (
    <div>
      <div className="flex items-center gap-4">
        <Link
          to="/crimes"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Back to Crimes & FIRs
        </Link>

        {canWrite && (
          <Link
            to={`/firs/${id}/edit`}
            className="text-sm text-blue-600 hover:underline"
          >
            Edit
          </Link>
        )}
      </div>

      <h1 className="text-2xl font-bold mt-2">{fir.fir_number}</h1>
      <p className="text-slate-600 mt-1">{fir.summary}</p>

      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div>
          <span className="text-slate-400">Station:</span> {fir.police_station_name}
        </div>

        <div>
          <span className="text-slate-400">Status:</span> {fir.status.replace(/_/g, ' ')}
        </div>

        <div>
          <span className="text-slate-400">Incident date:</span> {fir.incident_date}
        </div>

        <div>
          <span className="text-slate-400">Filed:</span>{' '}
          {new Date(fir.date_filed).toLocaleString()}
        </div>

        <div>
          <span className="text-slate-400">Location:</span> {fir.incident_location}
        </div>

        <div>
          <span className="text-slate-400">Registered by:</span> {fir.registered_by_name}
        </div>

        <div>
          <span className="text-slate-400">Complainant:</span> {fir.complainant_name}
        </div>

        <div>
          <span className="text-slate-400">Phone:</span> {fir.complainant_phone}
        </div>
      </div>

      <h2 className="text-lg font-semibold mt-6 mb-2">Linked Crimes</h2>

      {linkedCrimes.length === 0 && (
        <p className="text-slate-500 text-sm">No linked crimes.</p>
      )}

      <div className="space-y-2">
        {linkedCrimes.map((link) => (
          <Card key={link.id}>
            <CardContent className="p-3 flex justify-between items-center">
              <span>{link.crime_category_name}</span>

              {link.is_primary_offense && (
                <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                  Primary offense
                </span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}