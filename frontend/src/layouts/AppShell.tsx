import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { usePermissions } from '../hooks/usePermissions'
import kspEmblem from '../assets/ksp-emblem.jpg'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/crimes', label: 'Crimes & FIRs' },
  { to: '/investigations', label: 'Investigations' },
  { to: '/persons', label: 'Persons' },
  { to: '/assets', label: 'Assets' },
  { to: '/assistant', label: 'AI Assistant' },
]

export function AppShell() {
  const officer = useAuth((s) => s.officer)
  const clearAuth = useAuth((s) => s.clearAuth)
  const { isStateScoped, isStationScoped, canWrite } = usePermissions()

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col">
        <div className="p-4 flex items-center gap-3 border-b border-slate-700">
        <img src={kspEmblem} alt="" className="w-8 h-8 rounded" />
        <span className="text-lg font-bold">KSP Insight AI</span>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${
                  isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}

          {/* Station Officer+ only, per spec §5 */}
          {canWrite && (
            <NavLink
              to="/administration"
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${
                  isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              Administration
            </NavLink>
          )}

          {/* Full state-wide log for DGP/SCRB Analyst; station-wide for
              Constable/Station Officer; own-activity only otherwise —
              the backend already scopes rows this way (see
              AuditLogViewSet.get_queryset), so it's visible to every role */}
          <NavLink
            to="/audit-log"
            className={({ isActive }) =>
              `block rounded px-3 py-2 text-sm ${
                isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'
              }`
            }
          >
            {isStateScoped ? 'Audit Log' : isStationScoped ? 'Station Activity' : 'My Activity'}
          </NavLink>
        </nav>
        <div className="p-4 border-t border-slate-700 text-sm">
          <NavLink to="/profile" className="block hover:text-white">
            <div className="font-medium">{officer?.first_name} {officer?.last_name}</div>
            <div className="text-slate-400">{officer?.role_name}</div>
          </NavLink>
          <button onClick={clearAuth} className="mt-2 text-slate-400 hover:text-white underline">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 bg-slate-50 p-6">
        <Outlet />
      </main>
    </div>
  )
}
