import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { fetchCrimeById, fetchFIRCrimes } from '../../api/crimes'
import { usePermissions } from '../../hooks/usePermissions'

import { Card, CardContent } from '@/components/ui/card'

export function CrimeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { canWrite } = usePermissions()

  const {
    data: crime,
    isLoading: crimeLoading,
    error: crimeError,
  } = useQuery({
    queryKey: ['crime', id],
    queryFn: () => fetchCrimeById(id!),
    enabled: !!id,
  })

  const {
    data: allLinks,
    isLoading: linksLoading,
  } = useQuery({
    queryKey: ['fircrimes'],
    queryFn: fetchFIRCrimes,
  })

  if (crimeLoading || linksLoading) {
    return <p className="text-slate-500">Loading crime...</p>
  }

  if (crimeError || !crime) {
    return <p className="text-red-600">Failed to load crime.</p>
  }

  const linkedFIRs = allLinks?.filter((link) => link.crime === id) ?? []

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
            to={`/crimes/${id}/edit`}
            className="text-sm text-blue-600 hover:underline"
          >
            Edit
          </Link>
        )}
      </div>

      <h1 className="mt-2 text-2xl font-bold">
        {crime.category_name}
      </h1>

      <p className="mt-1 text-slate-600">
        {crime.description}
      </p>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-slate-400">Station:</span>{' '}
          {crime.police_station_name}
        </div>

        <div>
          <span className="text-slate-400">Status:</span>{' '}
          {crime.status.replace(/_/g, ' ')}
        </div>

        <div>
          <span className="text-slate-400">Date of occurrence:</span>{' '}
          {crime.date_of_occurrence}
        </div>

        <div>
          <span className="text-slate-400">Reported by:</span>{' '}
          {crime.reported_by_name}
        </div>

        {crime.location_description && (
          <div>
            <span className="text-slate-400">Location:</span>{' '}
            {crime.location_description}
          </div>
        )}
      </div>

      <h2 className="mt-6 mb-2 text-lg font-semibold">
        Linked FIRs
      </h2>

      {linkedFIRs.length === 0 && (
        <p className="text-sm text-slate-500">
          No linked FIRs.
        </p>
      )}

      <div className="space-y-2">
        {linkedFIRs.map((link) => (
          <Link key={link.id} to={`/firs/${link.fir}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="flex items-center justify-between p-3">
                <span>{link.fir_number}</span>

                {link.is_primary_offense && (
                  <span className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800">
                    Primary offense
                  </span>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}