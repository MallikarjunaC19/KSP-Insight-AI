import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createFIR, updateFIR, type FIR } from '../../api/crimes'
import { fetchPoliceStations } from '../../api/accounts'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'

const firSchema = z.object({
  fir_number: z.string().min(1, 'FIR number is required'),
  police_station: z.string().min(1, 'Police station is required'),
  complainant_name: z.string().min(1, 'Complainant name is required'),
  complainant_phone: z.string().optional(),
  incident_date: z.string().min(1, 'Incident date is required'),
  incident_location: z.string().min(1, 'Incident location is required'),
  summary: z.string().min(1, 'Summary is required'),
})

type FIRFormValues = z.infer<typeof firSchema>

interface FIRFormProps {
  existingFIR?: FIR
  onSuccess?: (fir: FIR) => void
}

export function FIRForm({ existingFIR, onSuccess }: FIRFormProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const officer = useAuth((s) => s.officer)

  const { data: stations } = useQuery({ queryKey: ['police-stations'], queryFn: fetchPoliceStations })

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FIRFormValues>({
    resolver: zodResolver(firSchema),
   defaultValues: existingFIR
  ? {
      fir_number: existingFIR.fir_number,
      police_station: existingFIR.police_station,
      complainant_name: existingFIR.complainant_name,
      complainant_phone: existingFIR.complainant_phone ?? '',
      incident_date: existingFIR.incident_date,
      incident_location: existingFIR.incident_location,
      summary: existingFIR.summary,
    }
  : {
      fir_number: '',
      police_station: '',
      complainant_name: '',
      complainant_phone: '',
      incident_date: '',
      incident_location: '',
      summary: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: FIRFormValues) =>
      existingFIR
        ? updateFIR(existingFIR.id, values)
        : createFIR({ ...values, registered_by: officer!.id }),
    onSuccess: (fir) => {
      queryClient.invalidateQueries({ queryKey: ['firs'] })
      if (onSuccess) onSuccess(fir)
      else navigate(`/firs/${fir.id}`)
    },
  })

  const selectedStation = watch('police_station')

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4 max-w-lg">
      <div>
        <Label>FIR Number</Label>
        <Input placeholder="e.g. CUB/2026/0104" {...register('fir_number')} />
        {errors.fir_number && <p className="text-sm text-red-600">{errors.fir_number.message}</p>}
      </div>

      <div>
        <Label>Police Station</Label>
        <Select value={selectedStation} onValueChange={(v) => setValue('police_station', v, { shouldValidate: true })}>
          <SelectTrigger><SelectValue placeholder="Select station" /></SelectTrigger>
          <SelectContent>
            {stations?.map((s) => (
              <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.police_station && <p className="text-sm text-red-600">{errors.police_station.message}</p>}
      </div>

      <div>
        <Label>Complainant Name</Label>
        <Input {...register('complainant_name')} />
        {errors.complainant_name && <p className="text-sm text-red-600">{errors.complainant_name.message}</p>}
      </div>

      <div>
        <Label>Complainant Phone</Label>
        <Input {...register('complainant_phone')} />
      </div>

      <div>
        <Label>Incident Date</Label>
        <input type="date" {...register('incident_date')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
        {errors.incident_date && <p className="text-sm text-red-600">{errors.incident_date.message}</p>}
      </div>

      <div>
        <Label>Incident Location</Label>
        <Input {...register('incident_location')} />
        {errors.incident_location && <p className="text-sm text-red-600">{errors.incident_location.message}</p>}
      </div>

      <div>
        <Label>Summary</Label>
        <Textarea {...register('summary')} />
        {errors.summary && <p className="text-sm text-red-600">{errors.summary.message}</p>}
      </div>

      {mutation.isError && (
        <p className="text-sm text-red-600">Failed to save: {(mutation.error as Error).message}</p>
      )}

      <Button type="submit" disabled={isSubmitting || mutation.isPending}>
        {mutation.isPending ? 'Saving...' : existingFIR ? 'Save Changes' : 'File FIR'}
      </Button>
    </form>
  )
}