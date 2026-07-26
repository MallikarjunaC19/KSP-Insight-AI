import { FIRForm } from './FIRForm'
import { Link } from 'react-router-dom'

export function FIRCreatePage() {
  return (
    <div>
      <Link to="/crimes" className="text-sm text-blue-600 hover:underline">← Back to Crimes & FIRs</Link>
      <h1 className="text-2xl font-bold mt-2 mb-4">New FIR</h1>
      <FIRForm />
    </div>
  )
}