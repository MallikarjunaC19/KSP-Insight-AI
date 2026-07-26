import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, { Background, Controls, type Node, type Edge } from 'reactflow'
import 'reactflow/dist/style.css'
import { fetchPersonCaseRoles } from '../../api/persons'
import { fetchVehicles } from '../../api/assets'

export function PersonNetworkGraph({ personId, personName }: { personId: string; personName: string }) {
  const { data: allRoles, isLoading: rolesLoading } = useQuery({ queryKey: ['person-case-roles'], queryFn: fetchPersonCaseRoles })
  const { data: allVehicles, isLoading: vehiclesLoading } = useQuery({ queryKey: ['vehicles'], queryFn: fetchVehicles })

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = []
    const edges: Edge[] = []
    const personNodeId = `person-${personId}`

    nodes.push({
      id: personNodeId,
      position: { x: 400, y: 50 },
      data: { label: personName },
      style: { background: '#1e3a5f', color: 'white', fontWeight: 600, borderRadius: 8 },
    })

    const roles = allRoles?.filter((r) => r.person === personId) ?? []
    roles.forEach((role, i) => {
      const caseNodeId = `case-${role.case}`
      nodes.push({
        id: caseNodeId,
        position: { x: 150 + i * 200, y: 200 },
        data: { label: `${role.case_number}\n(${role.role})` },
        style: { background: role.role === 'SUSPECT' ? '#fee2e2' : '#dbeafe', borderRadius: 8, whiteSpace: 'pre-line', fontSize: 12 },
      })
      edges.push({ id: `e-${personId}-${role.case}`, source: personNodeId, target: caseNodeId, label: role.role, animated: role.role === 'SUSPECT' })
    })

    const ownedVehicles = allVehicles?.filter((v) => v.ownerships.some((o) => o.owner === personId)) ?? []
    ownedVehicles.forEach((v, j) => {
      const vehicleNodeId = `vehicle-${v.id}`
      nodes.push({
        id: vehicleNodeId,
        position: { x: 150 + j * 200, y: 340 },
        data: { label: `${v.registration_number}\n${v.make} ${v.model}` },
        style: { background: '#fef3c7', borderRadius: 8, whiteSpace: 'pre-line', fontSize: 11 },
      })
      edges.push({ id: `e-${personId}-veh-${v.id}`, source: personNodeId, target: vehicleNodeId })
    })

    return { nodes, edges }
  }, [allRoles, allVehicles, personId, personName])

  if (rolesLoading || vehiclesLoading) return <p className="text-slate-500 text-sm">Loading network...</p>
  if (nodes.length <= 1) return <p className="text-slate-500 text-sm">No case or vehicle connections found for this person.</p>

  return (
    <div style={{ height: 350 }} className="border border-slate-200 rounded-lg">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}