import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchCrimeById } from '../../api/crimes'
import { CrimeForm } from './CrimeForm'

export function CrimeEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: crime, isLoading, error } = useQuery({
    queryKey: ['crime', id],
    queryFn: () => fetchCrimeById(id!),
    enabled: !!id,
  })

  if (isLoading) return <p className="text-slate-500">Loading crime...</p>
  if (error || !crime) return <p className="text-red-600">Failed to load crime.</p>

  return (
    <div>
      <Link to={`/crimes/${id}`} className="text-sm text-blue-600 hover:underline">← Back to Crime</Link>
      <h1 className="text-2xl font-bold mt-2 mb-4">Edit Crime</h1>
      <CrimeForm existingCrime={crime} onSuccess={() => navigate(`/crimes/${id}`)} />
    </div>
  )
}