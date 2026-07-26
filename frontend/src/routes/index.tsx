import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { CrimesAndFIRsPage } from '@/features/crimes/CrimesAndFIRsPage'
import { FIRDetailPage } from '@/features/firs/FIRDetailPage'
import { CrimeDetailPage } from '@/features/crimes/CrimeDetailPage'
import { CrimeCreatePage } from '@/features/crimes/CrimeCreatePage'
import { CrimeEditPage } from '@/features/crimes/CrimeEditPage'
import { FIRCreatePage } from '@/features/firs/FIRCreatePage'
import { FIREditPage } from '@/features/firs/FIREditPage'
import { InvestigationCasesListPage } from '@/features/investigations/InvestigationCasesListPage'
import { InvestigationCaseDetailPage } from '@/features/investigations/InvestigationCaseDetailPage'
import { PersonsListPage } from '../features/persons/PersonsListPage'
import { PersonDetailPage } from '../features/persons/PersonDetailPage'
import { AssetsPage } from '../features/assets/AssetsPage'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { AIAssistantPage } from '../features/assistant/AIAssistantPage'
import { AuditLogPage } from '../features/audit-log/AuditLogPage'
import { ProfilePage } from '../features/profile/ProfilePage'
import { AdministrationPage } from '../features/administration/AdministrationPage'
import { OfficerDetailPage } from '../features/administration/OfficerDetailPage'


export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'crimes', element: <CrimesAndFIRsPage /> },
      { path: 'assets', element: <AssetsPage /> },
      { path: 'firs/:id', element: <FIRDetailPage /> },
      { path: 'crimes/:id', element: <CrimeDetailPage /> },
      { path: 'crimes/new', element: <CrimeCreatePage /> },
      { path: 'crimes/:id/edit', element: <CrimeEditPage /> },
      { path: 'firs/new', element: <FIRCreatePage /> },
      { path: 'firs/:id/edit', element: <FIREditPage /> },
      { path: 'investigations', element: <InvestigationCasesListPage /> },
      { path: 'investigations/:id', element: <InvestigationCaseDetailPage /> },
      { path: 'persons', element: <PersonsListPage /> },
      { path: 'persons/:id', element: <PersonDetailPage /> },
      { path: 'assistant', element: <AIAssistantPage /> },
      { path: 'audit-log', element: <AuditLogPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'administration', element: <AdministrationPage /> },
      { path: 'administration/officers/:id', element: <OfficerDetailPage /> },
    ],
  },
])