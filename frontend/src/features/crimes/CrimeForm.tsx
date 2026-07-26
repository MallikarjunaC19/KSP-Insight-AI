import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchCrimeCategories, createCrime, updateCrime, type Crime } from '../../api/crimes'
import { fetchPoliceStations } from '../../api/accounts'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'

const crimeSchema = z.object({
  category: z.string().min(1, 'Category is required'),
  police_station: z.string().min(1, 'Police station is required'),
  description: z.string().min(1, 'Description is required'),
  date_of_occurrence: z.string().min(1, 'Date is required'),
  location_description: z.string().optional(),
})

type CrimeFormValues = z.infer<typeof crimeSchema>

interface CrimeFormProps {
  existingCrime?: Crime // pass this when editing
  onSuccess?: (crime: Crime) => void
}

export function CrimeForm({ existingCrime, onSuccess }: CrimeFormProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: categories } = useQuery({ queryKey: ['crime-categories'], queryFn: fetchCrimeCategories })
  const { data: stations } = useQuery({ queryKey: ['police-stations'], queryFn: fetchPoliceStations })

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CrimeFormValues>({
    resolver: zodResolver(crimeSchema),
   defaultValues: existingCrime
  ? {
      category: existingCrime.category,
      police_station: existingCrime.police_station,
      description: existingCrime.description,
      date_of_occurrence: existingCrime.date_of_occurrence,
      location_description: existingCrime.location_description ?? '',
    }
  : {
      category: '',
      police_station: '',
      description: '',
      date_of_occurrence: '',
      location_description: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: CrimeFormValues) =>
      existingCrime ? updateCrime(existingCrime.id, values) : createCrime(values),
    onSuccess: (crime) => {
      queryClient.invalidateQueries({ queryKey: ['crimes'] })
      if (onSuccess) onSuccess(crime)
      else navigate(`/crimes/${crime.id}`)
    },
  })

  const selectedCategory = watch('category')
  const selectedStation = watch('police_station')

  return (
    <form onSubmit={handleSubmit((values) => mutation.mutate(values))} className="space-y-4 max-w-lg">
      <div>
        <Label>Category</Label>
        <Select value={selectedCategory} onValueChange={(v) => setValue('category', v, { shouldValidate: true })}>
          <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
          <SelectContent>
            {categories?.map((c) => (
              <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.category && <p className="text-sm text-red-600">{errors.category.message}</p>}
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
        <Label>Description</Label>
        <Textarea {...register('description')} />
        {errors.description && <p className="text-sm text-red-600">{errors.description.message}</p>}
      </div>

      <div>
        <Label>Date of Occurrence</Label>
        <input type="date" {...register('date_of_occurrence')} className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm" />
        {errors.date_of_occurrence && <p className="text-sm text-red-600">{errors.date_of_occurrence.message}</p>}
      </div>

      <div>
        <Label>Location Description</Label>
        <Textarea {...register('location_description')} />
      </div>

      {mutation.isError && (
        <p className="text-sm text-red-600">Failed to save: {(mutation.error as Error).message}</p>
      )}

      <Button type="submit" disabled={isSubmitting || mutation.isPending}>
        {mutation.isPending ? 'Saving...' : existingCrime ? 'Save Changes' : 'Create Crime'}
      </Button>
    </form>
  )
}