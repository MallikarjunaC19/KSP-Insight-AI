import { useQuery } from '@tanstack/react-query'
import { fetchOfficers, fetchPoliceStations } from '../../api/accounts'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Link } from 'react-router-dom'

function OfficersTab() {
  const { data: officers, isLoading, error } = useQuery({ queryKey: ['officers'], queryFn: fetchOfficers })
  if (isLoading) return <p className="text-slate-500">Loading officers...</p>
  if (error) return <p className="text-red-600">Failed to load officers.</p>

  return (
    <div className="space-y-2">
      {officers?.map((o) => (
        <Link key={o.id} to={`/administration/officers/${o.id}`}>
          <Card className="hover:bg-slate-50 transition-colors">
            <CardContent className="p-3 flex justify-between items-center">
              <div>
                <span className="font-medium">{o.first_name} {o.last_name}</span>
                <span className="text-slate-400 text-sm ml-2">{o.badge_number}</span>
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
      {officers?.length === 0 && <p className="text-slate-500">No officers found.</p>}
    </div>
  )
}

function StationsTab() {
  const { data: stations, isLoading, error } = useQuery({ queryKey: ['police-stations'], queryFn: fetchPoliceStations })
  if (isLoading) return <p className="text-slate-500">Loading stations...</p>
  if (error) return <p className="text-red-600">Failed to load stations.</p>

  return (
    <div className="space-y-2">
      {stations?.map((s) => (
        <Card key={s.id}>
          <CardContent className="p-3">
            <span className="font-medium">{s.name}</span>
          </CardContent>
        </Card>
      ))}
      {stations?.length === 0 && <p className="text-slate-500">No stations found.</p>}
    </div>
  )
}

export function AdministrationPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Administration</h1>
      <Tabs defaultValue="officers">
        <TabsList>
          <TabsTrigger value="officers">Officers</TabsTrigger>
          <TabsTrigger value="stations">Stations</TabsTrigger>
        </TabsList>
        <TabsContent value="officers"><OfficersTab /></TabsContent>
        <TabsContent value="stations"><StationsTab /></TabsContent>
      </Tabs>
    </div>
  )
}