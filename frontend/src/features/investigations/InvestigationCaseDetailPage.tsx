import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  fetchInvestigationCaseById,
  fetchInvestigations,
  fetchInvestigationSteps,
  fetchArrests,
  fetchChargesheets,
  fetchCourtCases,
} from '../../api/investigations'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { usePermissions } from '../../hooks/usePermissions'
import { AddPhaseForm } from './AddPhaseForm'
import { AddStepForm } from './AddStepForm'
import { AddArrestForm } from './AddArrestForm'
import { AddChargesheetForm } from './AddChargesheetForm'
import { AddCourtCaseForm } from './AddCourtCaseForm'
import { CaseNetworkGraph } from './CaseNetworkGraph'

export function InvestigationCaseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { canWrite } = usePermissions()

  const {
    data: caseData,
    isLoading: caseLoading,
    error: caseError,
  } = useQuery({
    queryKey: ['investigation-case', id],
    queryFn: () => fetchInvestigationCaseById(id!),
    enabled: !!id,
  })

  const {
    data: allInvestigations,
    isLoading: invLoading,
  } = useQuery({
    queryKey: ['investigations'],
    queryFn: fetchInvestigations,
  })

  const {
    data: allSteps,
    isLoading: stepsLoading,
  } = useQuery({
    queryKey: ['investigation-steps'],
    queryFn: fetchInvestigationSteps,
  })

  const {
    data: allArrests,
    isLoading: arrestsLoading,
  } = useQuery({
    queryKey: ['arrests'],
    queryFn: fetchArrests,
  })

  const {
    data: allChargesheets,
    isLoading: chargesheetsLoading,
  } = useQuery({
    queryKey: ['chargesheets'],
    queryFn: fetchChargesheets,
  })

  const {
    data: allCourtCases,
    isLoading: courtCasesLoading,
  } = useQuery({
    queryKey: ['court-cases'],
    queryFn: fetchCourtCases,
  })

  if (caseLoading) {
    return <p className="text-slate-500">Loading case...</p>
  }

  if (caseError || !caseData) {
    return (
      <p className="text-red-600">
        Failed to load investigation case.
      </p>
    )
  }

  const phases = allInvestigations?.filter((inv) => inv.case === id) ?? []
  const arrests = allArrests?.filter((a) => a.case === id) ?? []
  const chargesheets =
    allChargesheets?.filter((cs) => cs.case === id) ?? []

  const chargesheetIds = chargesheets.map((cs) => cs.id)

  const courtCases =
    allCourtCases?.filter((cc) =>
      chargesheetIds.includes(cc.chargesheet)
    ) ?? []

  const anyLoading =
    invLoading ||
    stepsLoading ||
    arrestsLoading ||
    chargesheetsLoading ||
    courtCasesLoading

  return (
    <div>
      <Link
        to="/investigations"
        className="text-sm text-blue-600 hover:underline"
      >
        ← Back to Investigations
      </Link>

      <div className="flex justify-between items-center mt-2">
        <h1 className="text-2xl font-bold">
          {caseData.case_number}
        </h1>

        {canWrite && <AddPhaseForm caseId={id!} />}
      </div>

      <p className="text-slate-600 mt-1">
        FIR {caseData.fir_number} · Lead: {caseData.lead_officer_name}
      </p>

      {anyLoading ? (
        <p className="text-slate-500 mt-4">
          Loading case details...
        </p>
      ) : (
        <Tabs defaultValue="overview" className="mt-4">
          <TabsList>
            <TabsTrigger value="overview">
              Overview
            </TabsTrigger>
            <TabsTrigger value="phases">
              Phases & Diary
            </TabsTrigger>
            <TabsTrigger value="arrests">
              Arrests
            </TabsTrigger>
            <TabsTrigger value="chargesheets">
              Chargesheets
            </TabsTrigger>
            <TabsTrigger value="court">
              Court Cases
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid grid-cols-2 gap-4 text-sm mt-2">
              <div>
                <span className="text-slate-400">Status:</span>{' '}
                {caseData.status}
              </div>

              <div>
                <span className="text-slate-400">Priority:</span>{' '}
                {caseData.priority}
              </div>

              <div>
                <span className="text-slate-400">Opened:</span>{' '}
                {caseData.opened_date}
              </div>

              <div>
                <span className="text-slate-400">Closed:</span>{' '}
                {caseData.closed_date ?? '—'}
              </div>

              {caseData.summary && (
                <div className="col-span-2">
                  <span className="text-slate-400">
                    Summary:
                  </span>{' '}
                  {caseData.summary}
                </div>
              )}
            </div>
            <h2 className="text-lg font-semibold mt-6 mb-2">Case Network</h2>
            <CaseNetworkGraph caseId={caseData.id} caseNumber={caseData.case_number} />
          </TabsContent>

          <TabsContent value="phases">
            {phases.length === 0 && (
              <p className="text-slate-500 text-sm mt-2">
                No investigation phases yet.
              </p>
            )}

            <div className="space-y-4 mt-2">
              {phases.map((phase) => {
                const steps =
                  allSteps?.filter(
                    (s) => s.investigation === phase.id
                  ) ?? []

                return (
                  <Card key={phase.id}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold">
                            {phase.officer_name}
                          </div>

                          <div className="text-xs text-slate-400">
                            {phase.start_date} →{' '}
                            {phase.end_date ?? 'ongoing'}
                          </div>
                        </div>

                        <span className="text-xs px-2 py-1 rounded bg-amber-100 text-amber-800">
                          {phase.status}
                        </span>
                      </div>

                      {phase.findings && (
                        <p className="text-sm text-slate-600 mt-2">
                          {phase.findings}
                        </p>
                      )}

                      {canWrite && (
                        <div className="mt-2">
                          <AddStepForm
                            investigationId={phase.id}
                          />
                        </div>
                      )}

                      {steps.length > 0 && (
                        <div className="mt-3 border-l-2 border-slate-200 pl-4 space-y-2">
                          {steps
                            .sort(
                              (a, b) =>
                                new Date(
                                  a.step_date
                                ).getTime() -
                                new Date(
                                  b.step_date
                                ).getTime()
                            )
                            .map((step) => (
                              <div
                                key={step.id}
                                className="text-sm"
                              >
                                <span className="text-slate-400 text-xs">
                                  {new Date(
                                    step.step_date
                                  ).toLocaleString()}{' '}
                                  — {step.performed_by_name}
                                </span>

                                <p>{step.description}</p>
                              </div>
                            ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </TabsContent>

          <TabsContent value="arrests">

            {canWrite && <div className="mt-2 mb-2"><AddArrestForm caseId={id!} /></div>}   
                
            {arrests.length === 0 && (
              <p className="text-slate-500 text-sm mt-2">
                No arrests recorded.
              </p>
            )}

            <div className="space-y-3 mt-2">
              {arrests.map((arrest) => (
                <Card key={arrest.id}>
                  <CardContent className="p-4">
                    <div className="font-semibold">
                      {arrest.arrested_person_name}
                    </div>

                    <div className="text-xs text-slate-400 mt-1">
                      Arrested{' '}
                      {new Date(
                        arrest.arrest_date
                      ).toLocaleString()}{' '}
                      at {arrest.arrest_location} by{' '}
                      {arrest.arresting_officer_name}
                    </div>

                    {arrest.remarks && (
                      <p className="text-sm text-slate-600 mt-2">
                        {arrest.remarks}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="chargesheets">
            {canWrite && <div className="mt-2 mb-2"><AddChargesheetForm caseId={id!} /></div>}
            {chargesheets.length === 0 && (
              <p className="text-slate-500 text-sm mt-2">
                No chargesheets filed.
              </p>
            )}

            <div className="space-y-3 mt-2">
              {chargesheets.map((cs) => (
                <Card key={cs.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold">
                          {cs.sections_summary}
                        </div>

                        <div className="text-xs text-slate-400 mt-1">
                          Filed {cs.filing_date} by{' '}
                          {cs.filed_by_name}
                        </div>
                      </div>

                      <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                        {cs.status}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="court">
            {canWrite && chargesheets.length > 0 && (
              <div className="mt-2 mb-2 space-y-1">
                {chargesheets.map((cs) => (
                  <div key={cs.id} className="flex items-center gap-2 text-sm text-slate-500">
                    <span>{cs.sections_summary}:</span>
                    <AddCourtCaseForm chargesheetId={cs.id} />
                  </div>
                ))}
              </div>
            )}
            {courtCases.length === 0 && (
              <p className="text-slate-500 text-sm mt-2">
                No court cases yet.
              </p>
            )}

            <div className="space-y-3 mt-2">
              {courtCases.map((cc) => (
                <Card key={cc.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-semibold">
                          {cc.court_case_number}
                        </div>

                        <div className="text-sm text-slate-600">
                          {cc.court_name}
                        </div>

                        <div className="text-xs text-slate-400 mt-1">
                          Filed {cc.filing_date}
                          {cc.next_hearing_date &&
                            ` · Next hearing ${cc.next_hearing_date}`}
                        </div>

                        {cc.verdict && (
                          <div className="text-sm mt-1">
                            Verdict: {cc.verdict}
                          </div>
                        )}
                      </div>

                      <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-800">
                        {cc.status}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}