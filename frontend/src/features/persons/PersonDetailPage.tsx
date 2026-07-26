import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchPersonById, fetchPersonCaseRoles } from '../../api/persons'
import { Card, CardContent } from '@/components/ui/card'
import { PersonNetworkGraph } from './PersonNetworkGraph'

export function PersonDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: person, isLoading: personLoading, error: personError } = useQuery({
    queryKey: ['person', id],
    queryFn: () => fetchPersonById(id!),
    enabled: !!id,
  })

  const { data: allRoles, isLoading: rolesLoading } = useQuery({
    queryKey: ['person-case-roles'],
    queryFn: fetchPersonCaseRoles,
  })

  if (personLoading || rolesLoading) return <p className="text-slate-500">Loading person...</p>
  if (personError || !person) return <p className="text-red-600">Failed to load person.</p>

  const roles = allRoles?.filter((r) => r.person === id) ?? []
  const primaryPhone = person.phones.find((p) => p.is_primary) ?? person.phones[0]
  const primaryEmail = person.emails.find((e) => e.is_primary) ?? person.emails[0]
  const primaryAddress = person.addresses.find((a) => a.is_primary) ?? person.addresses[0]

  return (
    <div>
      <Link to="/persons" className="text-sm text-blue-600 hover:underline">← Back to Persons</Link>
      <h1 className="text-2xl font-bold mt-2">{person.first_name} {person.last_name}</h1>

      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div><span className="text-slate-400">Gender:</span> {person.gender}</div>
        <div><span className="text-slate-400">Date of Birth:</span> {person.date_of_birth ?? '—'}</div>
        <div><span className="text-slate-400">Nationality:</span> {person.nationality}</div>
        {person.occupation && <div><span className="text-slate-400">Occupation:</span> {person.occupation}</div>}
        {primaryPhone && <div><span className="text-slate-400">Phone:</span> {primaryPhone.phone_number}</div>}
        {primaryEmail && <div><span className="text-slate-400">Email:</span> {primaryEmail.email}</div>}
        {primaryAddress && (
          <div className="col-span-2">
            <span className="text-slate-400">Address:</span> {primaryAddress.address_line}, {primaryAddress.city}, {primaryAddress.district}, {primaryAddress.state} {primaryAddress.pincode}
          </div>
        )}
        {person.notes && <div className="col-span-2"><span className="text-slate-400">Notes:</span> {person.notes}</div>}
      </div>

      <h2 className="text-lg font-semibold mt-6 mb-2">Case Involvement</h2>
      {roles.length === 0 && <p className="text-slate-500 text-sm">No case involvement recorded.</p>}
      <div className="space-y-2">
        {roles.map((role) => (
          <Link key={role.id} to={`/investigations/${role.case}`}>
            <Card className="hover:bg-slate-50 transition-colors">
              <CardContent className="p-3 flex justify-between items-center">
                <div>
                  <span className="font-medium">{role.case_number}</span>
                  {role.remarks && <span className="text-slate-500 text-sm ml-2">{role.remarks}</span>}
                </div>
                <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-800">{role.role}</span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <h2 className="text-lg font-semibold mt-6 mb-2">Network</h2>
      <PersonNetworkGraph personId={person.id} personName={`${person.first_name} ${person.last_name}`} />
    </div>
  )
}