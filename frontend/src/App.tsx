import './App.css'
import { RouterProvider } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { router } from '@/routes'

import { LoginPage } from '@/features/auth/LoginPage'
import { useAuth } from '@/hooks/useAuth'

function App() {
  const officer = useAuth((s) => s.officer)

  return (
    <QueryClientProvider client={queryClient}>
      {officer ? <RouterProvider router={router} /> : <LoginPage />}
    </QueryClientProvider>
  )
}

export default App