import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, { Background, Controls, type Node, type Edge } from 'reactflow'
import 'reactflow/dist/style.css'
import { fetchPersonCaseRoles } from '../../api/persons'
import { fetchVehicles } from '../../api/assets'

export function CaseNetworkGraph({ caseId, caseNumber }: { caseId: string; caseNumber: string }) {
  const { data: allRoles, isLoading: rolesLoading } = useQuery({
    queryKey: ['person-case-roles'],
    queryFn: fetchPersonCaseRoles,
  })
  const { data: allVehicles, isLoading: vehiclesLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: fetchVehicles,
  })

  const { nodes, edges } = useMemo(() => {
    const roles = allRoles?.filter((r) => r.case === caseId) ?? []
    const nodes: Node[] = []
    const edges: Edge[] = []

    nodes.push({
      id: `case-${caseId}`,
      position: { x: 400, y: 50 },
      data: { label: caseNumber },
      style: { background: '#1e3a5f', color: 'white', fontWeight: 600, borderRadius: 8 },
    })

    roles.forEach((role, i) => {
      const personNodeId = `person-${role.person}`
      const x = 150 + i * 220
      nodes.push({
        id: personNodeId,
        position: { x, y: 200 },
        data: { label: `${role.person_name}\n(${role.role})` },
        style: { background: role.role === 'SUSPECT' ? '#fee2e2' : '#dbeafe', borderRadius: 8, whiteSpace: 'pre-line', fontSize: 12 },
      })
      edges.push({
        id: `e-case-${role.person}`,
        source: `case-${caseId}`,
        target: personNodeId,
        label: role.role,
        animated: role.role === 'SUSPECT',
      })

      const ownedVehicles = allVehicles?.filter((v) =>
        v.ownerships.some((o) => o.owner === role.person)
      ) ?? []
      ownedVehicles.forEach((v, j) => {
        const vehicleNodeId = `vehicle-${v.id}`
        if (!nodes.find((n) => n.id === vehicleNodeId)) {
          nodes.push({
            id: vehicleNodeId,
            position: { x: x - 40 + j * 80, y: 340 },
            data: { label: `${v.registration_number}\n${v.make} ${v.model}` },
            style: { background: '#fef3c7', borderRadius: 8, whiteSpace: 'pre-line', fontSize: 11 },
          })
        }
        edges.push({
          id: `e-${role.person}-${v.id}`,
          source: personNodeId,
          target: vehicleNodeId,
        })
      })
    })

    return { nodes, edges }
  }, [allRoles, allVehicles, caseId, caseNumber])

  if (rolesLoading || vehiclesLoading) return <p className="text-slate-500 text-sm">Loading network...</p>

  if (nodes.length <= 1) {
    return <p className="text-slate-500 text-sm">No persons linked to this case yet — network graph needs at least one PersonCaseRole entry.</p>
  }

  return (
    <div style={{ height: 400 }} className="border border-slate-200 rounded-lg">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}