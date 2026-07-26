import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchCrimes, fetchFIRs } from '../../api/crimes'
import { fetchInvestigationCases, fetchChargesheets } from '../../api/investigations'
import { useAuth } from '../../hooks/useAuth'
import { Card, CardContent } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

function StatCard({ label, value, to }: { label: string; value: number | string; to: string }) {
  return (
    <Link to={to}>
      <Card className="hover:bg-slate-50 transition-colors">
        <CardContent className="p-6">
          <div className="text-3xl font-bold">{value}</div>
          <div className="text-sm text-slate-500 mt-1">{label}</div>
        </CardContent>
      </Card>
    </Link>
  )
}

export function DashboardPage() {
  const officer = useAuth((s) => s.officer)

  const { data: crimes, isLoading: crimesLoading } = useQuery({ queryKey: ['crimes'], queryFn: fetchCrimes })
  const { data: firs, isLoading: firsLoading } = useQuery({ queryKey: ['firs'], queryFn: fetchFIRs })
  const { data: cases, isLoading: casesLoading } = useQuery({ queryKey: ['investigation-cases'], queryFn: fetchInvestigationCases })
  const { data: chargesheets, isLoading: chargesheetsLoading } = useQuery({ queryKey: ['chargesheets'], queryFn: fetchChargesheets })

  const isLoading = crimesLoading || firsLoading || casesLoading || chargesheetsLoading

  const openCases = cases?.filter((c) => c.status === 'OPEN' || c.status === 'UNDER_INVESTIGATION').length ?? 0
  const recentFIRs = firs?.filter((f) => {
    const filed = new Date(f.date_filed)
    const daysAgo = (Date.now() - filed.getTime()) / (1000 * 60 * 60 * 24)
    return daysAgo <= 30
  }).length ?? 0
  const pendingChargesheets = chargesheets?.filter((cs) => cs.status === 'DRAFT' || cs.status === 'FILED').length ?? 0
  const underInvestigationCrimes = crimes?.filter((c) => c.status === 'UNDER_INVESTIGATION').length ?? 0

  // Status breakdown chart data
  const statusCounts: Record<string, number> = {}
  crimes?.forEach((c) => {
    statusCounts[c.status] = (statusCounts[c.status] ?? 0) + 1
  })
  const chartData = Object.entries(statusCounts).map(([status, count]) => ({
    status: status.replace(/_/g, ' '),
    count,
  }))
  const statusColorMap: Record<string, string> = {
  'REPORTED': '#3b82f6',
  'UNDER INVESTIGATION': '#f59e0b',
  'CHARGESHEET FILED': '#8b5cf6',
  'CLOSED': '#10b981',
}

  // Recent activity: latest 5 FIRs and crimes combined, sorted by date
  type ActivityItem = { id: string; label: string; date: string; to: string }
  const activity: ActivityItem[] = [
    ...(firs?.map((f) => ({
      id: f.id,
      label: `FIR ${f.fir_number} filed — ${f.summary}`,
      date: f.date_filed,
      to: `/firs/${f.id}`,
    })) ?? []),
    ...(crimes?.map((c) => ({
      id: c.id,
      label: `${c.category_name} reported — ${c.description}`,
      date: c.created_at,
      to: `/crimes/${c.id}`,
    })) ?? []),
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">
        Welcome, {officer?.first_name} {officer?.last_name}
      </h1>
      <p className="text-slate-500 mb-6">{officer?.role_name} — {officer?.police_station_name}</p>

      {isLoading ? (
        <p className="text-slate-500">Loading dashboard...</p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Open Investigation Cases" value={openCases} to="/investigations" />
            <StatCard label="FIRs Filed (Last 30 Days)" value={recentFIRs} to="/crimes" />
            <StatCard label="Crimes Under Investigation" value={underInvestigationCrimes} to="/crimes" />
            <StatCard label="Pending Chargesheets" value={pendingChargesheets} to="/investigations" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
                <CardContent className="p-4">
                  <h2 className="text-sm font-semibold text-slate-500 mb-3">Crimes by Status</h2>
                  {chartData.length === 0 ? (
                    <p className="text-slate-500 text-sm">No crime data yet.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                          data={chartData}
                          dataKey="count"
                          nameKey="status"
                          innerRadius={55}
                          outerRadius={85}
                          paddingAngle={3}
                        >
                          {chartData.map((entry, i) => (
                            <Cell key={i} fill={statusColorMap[entry.status] ?? '#94a3b8'} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            <Card>
              <CardContent className="p-4">
                <h2 className="text-sm font-semibold text-slate-500 mb-3">Recent Activity</h2>
                {activity.length === 0 ? (
                  <p className="text-slate-500 text-sm">No recent activity.</p>
                ) : (
                  <div className="space-y-3">
                    {activity.map((item) => (
                      <Link key={item.id} to={item.to} className="block text-sm hover:bg-slate-50 -mx-2 px-2 py-1 rounded">
                        <div>{item.label}</div>
                        <div className="text-xs text-slate-400">{item.date.slice(0, 10)}</div>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}