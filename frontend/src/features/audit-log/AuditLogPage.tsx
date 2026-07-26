import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAuditLog, type AuditActionType, type AuditLogEntry } from '../../api/auditlog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { usePermissions } from '../../hooks/usePermissions'

// Confirmed against assistant/models.py AuditLog.ActionType — do not add/remove values
// without checking the model, since there's no server-side validation surfaced here.
const ACTION_TYPES: AuditActionType[] = ['QUERY', 'LOGIN', 'DATA_ACCESS', 'EXPORT', 'OTHER']

interface Filters {
  action_type: AuditActionType | ''
  date_from: string // YYYY-MM-DD, from <input type="date">
  date_to: string
  search: string // free-text match against description / officer_name — client-side only
}

const EMPTY_FILTERS: Filters = { action_type: '', date_from: '', date_to: '', search: '' }

export function AuditLogPage() {
  const { isStateScoped, isStationScoped } = usePermissions()
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)

  // No django-filter or pagination on the backend (confirmed) — fetch the full
  // (already RBAC-scoped) array once and filter/paginate client-side, same
  // pattern used elsewhere in this codebase for unfiltered sub-entities.
  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-log'],
    queryFn: fetchAuditLog,
  })

  // Anyone seeing more than just their own rows (state-scoped or station-scoped)
  // benefits from the officer column and the name/description search box.
  const showsMultipleOfficers = isStateScoped || isStationScoped

  const pageTitle = isStateScoped
    ? 'Audit Log'
    : isStationScoped
    ? 'Station Activity'
    : 'My Activity'

  const pageDescription = isStateScoped
    ? 'Read-only record of officer actions and AI queries across the system.'
    : isStationScoped
    ? 'Read-only record of AI queries and data access at your station.'
    : 'A read-only record of your own AI queries and data access.'

  const filtered = useMemo(() => {
    if (!data) return []
    const search = filters.search.trim().toLowerCase()
    const fromMs = filters.date_from ? new Date(filters.date_from + 'T00:00:00').getTime() : null
    const toMs = filters.date_to ? new Date(filters.date_to + 'T23:59:59.999').getTime() : null

    return data.filter((entry) => {
      if (filters.action_type && entry.action_type !== filters.action_type) return false

      const created = new Date(entry.created_at).getTime()
      if (fromMs !== null && created < fromMs) return false
      if (toMs !== null && created > toMs) return false

      if (search) {
        const haystack = `${entry.description} ${entry.officer_name}`.toLowerCase()
        if (!haystack.includes(search)) return false
      }
      return true
    })
  }, [data, filters])

  function updateFilter<K extends keyof Filters>(key: K, value: Filters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">{pageTitle}</h1>
        <p className="text-sm text-slate-500">{pageDescription}</p>
      </div>

      {/* Filters — all client-side; the backend exposes no filter params on this endpoint */}
      <div className="flex flex-wrap gap-3 items-end border-b border-slate-100 pb-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Action type</label>
          <select
            className="border border-slate-300 rounded-md text-sm px-2 py-1.5"
            value={filters.action_type}
            onChange={(e) => updateFilter('action_type', e.target.value as AuditActionType | '')}
          >
            <option value="">All</option>
            {ACTION_TYPES.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">From</label>
          <Input type="date" value={filters.date_from} onChange={(e) => updateFilter('date_from', e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">To</label>
          <Input type="date" value={filters.date_to} onChange={(e) => updateFilter('date_to', e.target.value)} />
        </div>
        {showsMultipleOfficers && (
          <div>
            <label className="block text-xs text-slate-500 mb-1">Search</label>
            <Input
              placeholder="Officer name or description..."
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
            />
          </div>
        )}
        <Button variant="outline" size="sm" onClick={() => setFilters(EMPTY_FILTERS)}>
          Clear filters
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-400">Loading...</p>
      ) : isError ? (
        <p className="text-sm text-red-600">Failed to load audit log.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 pr-4 font-medium">Timestamp</th>
                {showsMultipleOfficers && <th className="py-2 pr-4 font-medium">Officer</th>}
                <th className="py-2 pr-4 font-medium">Action</th>
                <th className="py-2 pr-4 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry: AuditLogEntry) => (
                <tr key={entry.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-2 pr-4 text-slate-500 whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleString('en-IN', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </td>
                  {showsMultipleOfficers && <td className="py-2 pr-4">{entry.officer_name}</td>}
                  <td className="py-2 pr-4">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">
                      {entry.action_type}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-700">{entry.description}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={showsMultipleOfficers ? 4 : 3} className="py-6 text-center text-slate-400">
                    No matching entries.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {data && (
        <p className="text-xs text-slate-400">
          Showing {filtered.length} of {data.length} entries.
        </p>
      )}
    </div>
  )
}
