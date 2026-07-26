import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createCourtCase } from '../../api/investigations'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const courtCaseSchema = z.object({
  court_case_number: z.string().min(1, 'Court case number is required'),
  court_name: z.string().optional(),
  filing_date: z.string().min(1, 'Filing date is required'),
})
type CourtCaseFormValues = z.infer<typeof courtCaseSchema>

export function AddCourtCaseForm({ chargesheetId }: { chargesheetId: string }) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { register, handleSubmit, reset, formState: { errors } } = useForm<CourtCaseFormValues>({
    resolver: zodResolver(courtCaseSchema),
    defaultValues: { court_case_number: '', court_name: '', filing_date: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: CourtCaseFormValues) =>
      createCourtCase({ chargesheet: chargesheetId, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['court-cases'] })
      setOpen(false)
      reset()
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={ <Button variant="outline" size="sm" />  } >
        + Add Court Case
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>New Court Case</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-3">
          <div>
            <Label>Court Case Number</Label>
            <Input {...register('court_case_number')} placeholder="e.g. CC-2026-5502" />
            {errors.court_case_number && <p className="text-sm text-red-600">{errors.court_case_number.message}</p>}
          </div>
          <div>
            <Label>Court Name (optional)</Label>
            <Input {...register('court_name')} />
          </div>
          <div>
            <Label>Filing Date</Label>
            <input type="date" {...register('filing_date')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
            {errors.filing_date && <p className="text-sm text-red-600">{errors.filing_date.message}</p>}
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Failed: {(mutation.error as Error).message}</p>}
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Add Court Case'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}