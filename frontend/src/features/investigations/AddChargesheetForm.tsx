import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createChargesheet } from '../../api/investigations'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const chargesheetSchema = z.object({
  court_referred: z.string().optional(),
  filing_date: z.string().min(1, 'Filing date is required'),
  sections_summary: z.string().min(1, 'Sections summary is required'),
})
type ChargesheetFormValues = z.infer<typeof chargesheetSchema>

export function AddChargesheetForm({ caseId }: { caseId: string }) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const officer = useAuth((s) => s.officer)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ChargesheetFormValues>({
    resolver: zodResolver(chargesheetSchema),
    defaultValues: { court_referred: '', filing_date: '', sections_summary: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: ChargesheetFormValues) =>
      createChargesheet({ case: caseId, filed_by: officer!.id, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chargesheets'] })
      setOpen(false)
      reset()
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={ <Button variant="outline" size="sm" /> } >
        + Add Chargesheet
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>New Chargesheet</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-3">
          <div>
            <Label>Sections Summary</Label>
            <Textarea {...register('sections_summary')} placeholder="e.g. BNS Section 303 - Theft" />
            {errors.sections_summary && <p className="text-sm text-red-600">{errors.sections_summary.message}</p>}
          </div>
          <div>
            <Label>Filing Date</Label>
            <input type="date" {...register('filing_date')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
            {errors.filing_date && <p className="text-sm text-red-600">{errors.filing_date.message}</p>}
          </div>
          <div>
            <Label>Court Referred (optional)</Label>
            <Input {...register('court_referred')} placeholder="Court name as text" />
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Failed: {(mutation.error as Error).message}</p>}
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Add Chargesheet'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}