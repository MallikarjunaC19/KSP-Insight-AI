import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { CrimesListPage } from './CrimesListPage'
import { FIRsListPage } from '../firs/FIRsListPage'

export function CrimesAndFIRsPage() {
  return (
    <Tabs defaultValue="crimes">
      <TabsList>
        <TabsTrigger value="crimes">Crimes</TabsTrigger>
        <TabsTrigger value="firs">FIRs</TabsTrigger>
      </TabsList>
      <TabsContent value="crimes">
        <CrimesListPage />
      </TabsContent>
      <TabsContent value="firs">
        <FIRsListPage />
      </TabsContent>
    </Tabs>
  )
}