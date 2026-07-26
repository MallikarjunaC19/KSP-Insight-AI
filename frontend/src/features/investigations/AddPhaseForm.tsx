import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createInvestigation } from '../../api/investigations'
import { fetchOfficers } from '../../api/accounts'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const phaseSchema = z.object({
  officer: z.string().min(1, 'Officer is required'),
  findings: z.string().optional(),
})
type PhaseFormValues = z.infer<typeof phaseSchema>

export function AddPhaseForm({ caseId }: { caseId: string }) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { data: officers } = useQuery({ queryKey: ['officers'], queryFn: fetchOfficers })

  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<PhaseFormValues>({
  resolver: zodResolver(phaseSchema),
  defaultValues: { officer: '', findings: '' },
})

  const mutation = useMutation({
    mutationFn: (values: PhaseFormValues) => createInvestigation({ case: caseId, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigations'] })
      setOpen(false)
      reset()
    },
  })

  const selectedOfficer = watch('officer')

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" size="sm" />}>
        + Add Phase
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>New Investigation Phase</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-3">
          <div>
            <Label>Officer</Label>
            <Select value={selectedOfficer} onValueChange={(v) => setValue('officer', v ?? '', { shouldValidate: true })}>
              <SelectTrigger><SelectValue placeholder="Select officer" /></SelectTrigger>
              <SelectContent>
                {officers?.map((o) => (
                  <SelectItem key={o.id} value={o.id}>{o.first_name} {o.last_name} ({o.badge_number})</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.officer && <p className="text-sm text-red-600">{errors.officer.message}</p>}
          </div>
          <div>
            <Label>Findings (optional)</Label>
            <Textarea {...register('findings')} />
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Failed: {(mutation.error as Error).message}</p>}
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Add Phase'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}