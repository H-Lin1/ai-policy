import { createBrowserRouter } from 'react-router-dom'

import { AppLayout } from './AppLayout'
import { HealthPage } from './pages/HealthPage'
import { LoginPage } from './pages/LoginPage'
import { PolicyWorkspacePage } from './pages/PolicyWorkspacePage'
import { HistoricalQaWorkspacePage } from './pages/HistoricalQaWorkspacePage'
import { ClassificationWorkspacePage } from './pages/ClassificationWorkspacePage'
import { RoleWorkspacePage } from './pages/RoleWorkspacePage'
import { WorkspaceHomePage } from './pages/WorkspaceHomePage'
import { ConsultationWorkspacePage } from './pages/ConsultationWorkspacePage'
import { EnterpriseProfilePage } from './pages/EnterpriseProfilePage'
import { authenticatedHomePath, roleWorkspacePath } from './roleRoutes'
import { RegistrationPage } from './pages/RegistrationPage'
import { RegistrationStatusPage } from './pages/RegistrationStatusPage'
import { AdminRegistrationApplicationsPage } from './pages/AdminRegistrationApplicationsPage'
import { AdminRegistrationApplicationDetailPage } from './pages/AdminRegistrationApplicationDetailPage'
import { AdminPoliciesPage } from './pages/AdminPoliciesPage'
import { AdminPolicyEditorPage } from './pages/AdminPolicyEditorPage'
import { AdminAccountsPage } from './pages/AdminAccountsPage'
import { AdminAccountEditorPage } from './pages/AdminAccountEditorPage'

function NotFoundPage() {
  return (
    <section className="page-content empty-state">
      <div className="eyebrow">404</div>
      <h1>页面不存在</h1>
      <p>请从顶部导航返回工作区。</p>
    </section>
  )
}

const configuredBasePath = import.meta.env.VITE_APP_BASE_PATH?.trim() || '/'
const basename = configuredBasePath === '/' ? undefined : configuredBasePath.replace(/\/+$/, '')

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <WorkspaceHomePage /> },
      { path: authenticatedHomePath.slice(1), element: <WorkspaceHomePage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegistrationPage /> },
      { path: 'registration-status', element: <RegistrationStatusPage /> },
      { path: 'health', element: <HealthPage /> },
      { path: 'policies', element: <PolicyWorkspacePage /> },
      { path: 'policies/:policyId', element: <PolicyWorkspacePage /> },
      { path: 'qa', element: <HistoricalQaWorkspacePage /> },
      { path: 'qa/:qaId', element: <HistoricalQaWorkspacePage /> },
      { path: 'classify', element: <ClassificationWorkspacePage /> },
      { path: 'consultations', element: <ConsultationWorkspacePage /> },
      { path: 'consultations/new', element: <ConsultationWorkspacePage /> },
      { path: 'my-enterprise', element: <EnterpriseProfilePage /> },
      { path: roleWorkspacePath('individual').slice(1), element: <RoleWorkspacePage role="individual" /> },
      { path: roleWorkspacePath('enterprise').slice(1), element: <RoleWorkspacePage role="enterprise" /> },
      { path: roleWorkspacePath('government').slice(1), element: <RoleWorkspacePage role="government" /> },
      { path: 'registration-applications', element: <AdminRegistrationApplicationsPage /> },
      { path: 'registration-applications/:id', element: <AdminRegistrationApplicationDetailPage /> },
      { path: 'policy-management', element: <AdminPoliciesPage /> },
      { path: 'policy-management/new', element: <AdminPolicyEditorPage /> },
      { path: 'account-management', element: <AdminAccountsPage /> },
      { path: 'account-management/new', element: <AdminAccountEditorPage /> },
      { path: 'account-management/:userId', element: <AdminAccountEditorPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
], basename ? { basename } : undefined)
