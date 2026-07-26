import { CrimeForm } from './CrimeForm'
import { Link } from 'react-router-dom'

export function CrimeCreatePage() {
  return (
    <div>
      <Link to="/crimes" className="text-sm text-blue-600 hover:underline">← Back to Crimes & FIRs</Link>
      <h1 className="text-2xl font-bold mt-2 mb-4">New Crime</h1>
      <CrimeForm />
    </div>
  )
}