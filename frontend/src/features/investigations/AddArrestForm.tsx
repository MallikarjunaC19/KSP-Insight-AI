import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createArrest } from '../../api/investigations'
import { fetchOfficers } from '../../api/accounts'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const arrestSchema = z.object({
  arresting_officer: z.string().min(1, 'Officer is required'),
  arrested_person_name: z.string().min(1, 'Name is required'),
  arrested_person_details: z.string().optional(),
  arrest_date: z.string().min(1, 'Date/time is required'),
  arrest_location: z.string().optional(),
  remarks: z.string().optional(),
})
type ArrestFormValues = z.infer<typeof arrestSchema>

export function AddArrestForm({ caseId }: { caseId: string }) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()
  const { data: officers } = useQuery({ queryKey: ['officers'], queryFn: fetchOfficers })

  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<ArrestFormValues>({
    resolver: zodResolver(arrestSchema),
    defaultValues: {
      arresting_officer: '',
      arrested_person_name: '',
      arrested_person_details: '',
      arrest_date: '',
      arrest_location: '',
      remarks: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: ArrestFormValues) => createArrest({ case: caseId, ...values }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['arrests'] })
      setOpen(false)
      reset()
    },
  })

  const selectedOfficer = watch('arresting_officer')

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={ <Button variant="outline" size="sm" /> } >
       + Add Arrest
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>New Arrest</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-3">
          <div>
            <Label>Arresting Officer</Label>
            <Select value={selectedOfficer} onValueChange={(value) => setValue( 'arresting_officer', value ?? '',{ shouldValidate: true } )} >
              <SelectTrigger><SelectValue placeholder="Select officer" /></SelectTrigger>
              <SelectContent>
                {officers?.map((o) => (
                  <SelectItem key={o.id} value={o.id}>{o.first_name} {o.last_name} ({o.badge_number})</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.arresting_officer && <p className="text-sm text-red-600">{errors.arresting_officer.message}</p>}
          </div>
          <div>
            <Label>Arrested Person Name</Label>
            <Input {...register('arrested_person_name')} />
            {errors.arrested_person_name && <p className="text-sm text-red-600">{errors.arrested_person_name.message}</p>}
          </div>
          <div>
            <Label>Person Details (optional)</Label>
            <Textarea {...register('arrested_person_details')} placeholder="Age, address, ID details, etc." />
          </div>
          <div>
            <Label>Arrest Date & Time</Label>
            <input type="datetime-local" {...register('arrest_date')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
            {errors.arrest_date && <p className="text-sm text-red-600">{errors.arrest_date.message}</p>}
          </div>
          <div>
            <Label>Arrest Location (optional)</Label>
            <Input {...register('arrest_location')} />
          </div>
          <div>
            <Label>Remarks (optional)</Label>
            <Textarea {...register('remarks')} />
          </div>
          {mutation.isError && <p className="text-sm text-red-600">Failed: {(mutation.error as Error).message}</p>}
          <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving...' : 'Add Arrest'}</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}