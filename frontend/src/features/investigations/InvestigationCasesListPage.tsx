import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchInvestigationCases } from '../../api/investigations'
import { Card, CardContent } from '@/components/ui/card'

const statusColors: Record<string, string> = {
  OPEN: 'bg-blue-100 text-blue-800',
  ACTIVE: 'bg-amber-100 text-amber-800',
  CLOSED: 'bg-green-100 text-green-800',
}

const priorityColors: Record<string, string> = {
  HIGH: 'text-red-600',
  MEDIUM: 'text-amber-600',
  LOW: 'text-slate-500',
}

export function InvestigationCasesListPage() {
  const { data: cases, isLoading, error } = useQuery({
    queryKey: ['investigation-cases'],
    queryFn: fetchInvestigationCases,
  })

  if (isLoading) return <p className="text-slate-500">Loading investigation cases...</p>
  if (error) return <p className="text-red-600">Failed to load investigation cases.</p>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Investigations</h1>
      <div className="space-y-3">
        {cases?.map((c) => (
          <Link key={c.id} to={`/investigations/${c.id}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold">{c.case_number}</div>
                    <div className="text-sm text-slate-600">FIR {c.fir_number} · Lead: {c.lead_officer_name}</div>
                    <div className="text-xs text-slate-400 mt-1">Opened {c.opened_date}</div>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs px-2 py-1 rounded ${statusColors[c.status] ?? 'bg-slate-100 text-slate-800'}`}>
                      {c.status}
                    </span>
                    <div className={`text-xs mt-1 font-medium ${priorityColors[c.priority] ?? ''}`}>
                      {c.priority} priority
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {cases?.length === 0 && <p className="text-slate-500">No investigation cases found.</p>}
      </div>
    </div>
  )
}