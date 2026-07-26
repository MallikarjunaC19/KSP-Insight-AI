import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchFIRById } from '../../api/crimes'
import { FIRForm } from './FIRForm'

export function FIREditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: fir, isLoading, error } = useQuery({
    queryKey: ['fir', id],
    queryFn: () => fetchFIRById(id!),
    enabled: !!id,
  })

  if (isLoading) return <p className="text-slate-500">Loading FIR...</p>
  if (error || !fir) return <p className="text-red-600">Failed to load FIR.</p>

  return (
    <div>
      <Link to={`/firs/${id}`} className="text-sm text-blue-600 hover:underline">← Back to FIR</Link>
      <h1 className="text-2xl font-bold mt-2 mb-4">Edit FIR</h1>
      <FIRForm existingFIR={fir} onSuccess={() => navigate(`/firs/${id}`)} />
    </div>
  )
}