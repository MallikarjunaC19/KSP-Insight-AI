import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createInvestigationStep } from '../../api/investigations'
import { fetchOfficers } from '../../api/accounts'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const stepSchema = z.object({
  performed_by: z.string().min(1, 'Officer is required'),
  description: z.string().min(1, 'Description is required'),
  step_date: z.string().min(1, 'Date/time is required'),
})
type StepFormValues = z.infer<typeof stepSchema>

export function AddStepForm({ investigationId }: { investigationId: string }) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { data: officers } = useQuery({ queryKey: ['officers'], queryFn: fetchOfficers })

  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<StepFormValues>({
  resolver: zodResolver(stepSchema),
  defaultValues: { performed_by: '', description: '', step_date: '' },
})

  const mutation = useMutation({
    mutationFn: (values: StepFormValues) => createInvestigationStep({ investigation: investigationId, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigation-steps'] })
      setOpen(false)
      reset()
    },
  })

  const selectedOfficer = watch('performed_by')

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="ghost" size="sm" />}>
  + Add Diary Entry
</DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>New Diary Entry</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-3">
          <div>
            <Label>Performed By</Label>
            <Select value={selectedOfficer} onValueChange={(v) => setValue('performed_by', v ?? '', { shouldValidate: true })}>
              <SelectTrigger><SelectValue placeholder="Select officer" /></SelectTrigger>
              <SelectContent>
                {officers?.map((o) => (
                  <SelectItem key={o.id} value={o.id}>{o.first_name} {o.last_name} ({o.badge_number})</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.performed_by && <p className="text-sm text-red-600">{errors.performed_by.message}</p>}
          </div>
          <div>
            <Label>Description</Label>
            <Textarea {...register('description')} />
            {errors.description && <p className="text-sm text-red-600">{errors.description.message}</p>}
          </div>
          <div>
            <Label>Date & Time</Label>
            <input type="datetime-local" {...register('step_date')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
            {errors.step_date && <p className="text-sm text-red-600">{errors.step_date.message}</p>}
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Failed: {(mutation.error as Error).message}</p>}
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Add Entry'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}