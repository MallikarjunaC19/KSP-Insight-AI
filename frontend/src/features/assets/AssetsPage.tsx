import { useQuery } from '@tanstack/react-query'
import { fetchVehicles, fetchProperties, fetchWeapons } from '../../api/assets'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'

const statusColors: Record<string, string> = {
  ACTIVE: 'bg-green-100 text-green-800',
  REPORTED_STOLEN: 'bg-red-100 text-red-800',
  SEIZED: 'bg-amber-100 text-amber-800',
  ILLEGAL: 'bg-red-100 text-red-800',
}

function VehiclesTab() {
  const { data: vehicles, isLoading, error } = useQuery({ queryKey: ['vehicles'], queryFn: fetchVehicles })
  if (isLoading) return <p className="text-slate-500">Loading vehicles...</p>
  if (error) return <p className="text-red-600">Failed to load vehicles.</p>

  return (
    <div className="space-y-3">
      {vehicles?.map((v) => {
        const current = v.ownerships.find((o) => o.ownership_type === 'CURRENT') ?? v.ownerships[0]
        return (
          <Card key={v.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold">{v.registration_number} — {v.make} {v.model}</div>
                  <div className="text-sm text-slate-600">{v.vehicle_type}{v.color && ` · ${v.color}`}</div>
                  {current && (
                    <div className="text-xs text-slate-400 mt-1">Current owner: {current.owner_name}</div>
                  )}
                </div>
                <span className={`text-xs px-2 py-1 rounded ${v.is_stolen ? 'bg-red-100 text-red-800' : statusColors[v.status] ?? 'bg-slate-100 text-slate-800'}`}>
                  {v.is_stolen ? 'STOLEN' : v.status}
                </span>
              </div>

              {v.ownerships.length > 0 && (
                <div className="mt-3 border-l-2 border-slate-200 pl-4 space-y-1">
                  <div className="text-xs font-medium text-slate-500">Ownership History</div>
                  {v.ownerships
                    .sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime())
                    .map((o) => (
                      <div key={o.id} className="text-sm">
                        {o.owner_name} · {o.ownership_type} · {o.start_date} → {o.end_date ?? 'present'}
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
      {vehicles?.length === 0 && <p className="text-slate-500">No vehicles found.</p>}
    </div>
  )
}

function PropertiesTab() {
  const { data: properties, isLoading, error } = useQuery({ queryKey: ['properties'], queryFn: fetchProperties })
  if (isLoading) return <p className="text-slate-500">Loading properties...</p>
  if (error) return <p className="text-red-600">Failed to load properties.</p>

  return (
    <div className="space-y-3">
      {properties?.map((p) => (
        <Card key={p.id}>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold">{p.property_type}</div>
                <div className="text-sm text-slate-600">{p.description}</div>
                <div className="text-xs text-slate-400 mt-1">
                  ₹{Number(p.estimated_value).toLocaleString('en-IN')}
                  {p.owner_name && ` · Owner: ${p.owner_name}`}
                  {p.case_number && ` · Case ${p.case_number}`}
                </div>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${statusColors[p.status] ?? 'bg-slate-100 text-slate-800'}`}>
                {p.status.replace(/_/g, ' ')}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
      {properties?.length === 0 && <p className="text-slate-500">No properties found.</p>}
    </div>
  )
}

function WeaponsTab() {
  const { data: weapons, isLoading, error } = useQuery({ queryKey: ['weapons'], queryFn: fetchWeapons })
  if (isLoading) return <p className="text-slate-500">Loading weapons...</p>
  if (error) return <p className="text-red-600">Failed to load weapons.</p>

  return (
    <div className="space-y-3">
      {weapons?.map((w) => (
        <Card key={w.id}>
          <CardContent className="p-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold">{w.weapon_type}</div>
                <div className="text-sm text-slate-600">{w.description}</div>
                <div className="text-xs text-slate-400 mt-1">
                  {w.owner_name && `Owner: ${w.owner_name} · `}
                  {w.case_number && `Case ${w.case_number}`}
                </div>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${statusColors[w.status] ?? 'bg-slate-100 text-slate-800'}`}>
                {w.status}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
      {weapons?.length === 0 && <p className="text-slate-500">No weapons found.</p>}
    </div>
  )
}

export function AssetsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Assets</h1>
      <Tabs defaultValue="vehicles">
        <TabsList>
          <TabsTrigger value="vehicles">Vehicles</TabsTrigger>
          <TabsTrigger value="properties">Properties</TabsTrigger>
          <TabsTrigger value="weapons">Weapons</TabsTrigger>
        </TabsList>
        <TabsContent value="vehicles"><VehiclesTab /></TabsContent>
        <TabsContent value="properties"><PropertiesTab /></TabsContent>
        <TabsContent value="weapons"><WeaponsTab /></TabsContent>
      </Tabs>
    </div>
  )
}