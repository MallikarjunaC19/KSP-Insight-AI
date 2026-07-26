import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchPersons } from '../../api/persons'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export function PersonsListPage() {
  const [search, setSearch] = useState('')
  const { data: persons, isLoading, error } = useQuery({
    queryKey: ['persons'],
    queryFn: fetchPersons,
  })

  if (isLoading) return <p className="text-slate-500">Loading persons...</p>
  if (error) return <p className="text-red-600">Failed to load persons.</p>

  const filtered = persons?.filter((p) =>
    `${p.first_name} ${p.last_name}`.toLowerCase().includes(search.toLowerCase())
  ) ?? []

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Persons</h1>
      <Input
        placeholder="Search by name..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-sm"
      />
      <div className="space-y-3">
        {filtered.map((person) => (
          <Link key={person.id} to={`/persons/${person.id}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="p-4">
                <div className="font-semibold">{person.first_name} {person.last_name}</div>
                <div className="text-xs text-slate-400 mt-1">
                  {person.gender} · {person.date_of_birth ?? 'DOB unknown'} · {person.nationality}
                  {person.phones[0] && ` · ${person.phones[0].phone_number}`}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {filtered.length === 0 && <p className="text-slate-500">No persons found.</p>}
      </div>
    </div>
  )
}