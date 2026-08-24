export interface HealthResponse {
  status?: 'ok' | 'ready' | 'degraded' | string
  service?: string
  version?: string
  environment?: string
  checks?: Record<string, unknown>
  [key: string]: unknown
}

export interface ApiErrorDetail {
  code: string
  message: string
  details: unknown
}

export interface ApiErrorResponse {
  error: ApiErrorDetail
  request_id: string
}

export interface FeaturesResponse {
  environment: string
  auth_required: boolean
  features: Record<string, boolean>
}

export type RoleCode = 'individual' | 'enterprise' | 'government' | 'admin'

export interface RoleSummary {
  code: string
  name: string
}

export interface RegionSummary {
  code: string
  name: string
}

export interface OrganizationSummary {
  code: string
  name: string
  organization_type: string
}

export interface MeResponse {
  subject: string
  email?: string | null
  display_name: string
  roles: string[]
  role_summaries: RoleSummary[]
  region?: RegionSummary | null
  organization?: OrganizationSummary | null
  development_bypass: boolean
}

export interface WorkspaceResponse {
  role: RoleCode
  title: string
  subject: string
  region?: RegionSummary | null
  organization?: OrganizationSummary | null
}

export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface PageResponse<T> {
  items: T[]
  meta: PaginationMeta
}

export interface PolicyListItem {
  id: string
  title: string
  document_no?: string | null
  issuing_organization?: string | null
  source_url: string
  published_date?: string | null
  effective_status?: string | null
}

export interface PolicyDetail extends PolicyListItem {
  document_url?: string | null
  collected_at: UtcDateTimeString
  content_text: string
  content_sha256: string
  requested_title?: string | null
  reference_count?: number | null
  source_years?: string | null
}

export interface HistoricalQaListItem {
  id: string
  topic: string
  source_url: string
  replied_at?: UtcDateTimeString | null
  publishing_organization: string
  contains_legal_basis: boolean
}

export interface HistoricalQaDetail extends HistoricalQaListItem {
  question_text: string
  answer_text: string
  question_at?: UtcDateTimeString | null
  collected_at: UtcDateTimeString
  legal_basis_name?: string | null
  legal_basis_citation?: string | null
  adjudication_result: string
  content_sha256: string
}

export interface ClassificationPrediction {
  department_id: string
  department_name: string
  confidence: number
}

export interface ClassificationResponse {
  region_id: string
  model_version: string
  predictions: ClassificationPrediction[]
}

export interface ConsultationDepartment {
  department_id: string
  department_name: string
}

export interface ConsultationPrediction extends ConsultationDepartment {
  confidence: number
}

export interface ConsultationRecord {
  id: string
  selected_department: ConsultationDepartment
  status: 'assigned' | 'closed'
  question_text: string
  recommendations: ConsultationPrediction[]
  created_at: UtcDateTimeString
  assigned_at: UtcDateTimeString
  answer_text?: string | null
  publish_to_history: boolean
  historical_qa_id?: string | null
  replied_at?: UtcDateTimeString | null
  closed_at?: UtcDateTimeString | null
}

export type PolicyAnswerMode = 'placeholder' | 'rag'

export interface PolicyAnswerSource {
  source_type: 'policy_document' | 'historical_qa'
  source_id: string
  title: string
  source_url: string
  published_date?: string | null
  excerpt?: string | null
}

export interface PolicyAnswerResponse {
  request_id: string
  region_id: 'sz'
  answer_mode: PolicyAnswerMode
  answer: string
  sources: PolicyAnswerSource[]
  notices: string[]
}

export type UtcDateTimeString = string

interface LegacyErrorResponse {
  error?: Partial<ApiErrorDetail>
  request_id?: string
  detail?: string
  message?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly details?: unknown
  readonly requestId?: string

  constructor(
    message: string,
    status: number,
    options: { code?: string; details?: unknown; requestId?: string } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = options.code
    this.details = options.details
    this.requestId = options.requestId
  }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const baseUrl = configuredBaseUrl.replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path.startsWith('/') ? path : `/${path}`}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let detail = response.statusText || '请求失败'
    let code: string | undefined
    let details: unknown
    let requestId = response.headers.get('X-Request-ID') ?? undefined
    try {
      const body = (await response.json()) as LegacyErrorResponse
      detail = body.error?.message ?? body.detail ?? body.message ?? detail
      code = body.error?.code
      details = body.error?.details
      requestId = body.request_id ?? requestId
      if (code) detail = `${code}: ${detail}`
    } catch {
      // Keep the HTTP status text when the server does not return JSON.
    }
    throw new ApiError(`${detail}（${response.status}）`, response.status, {
      code,
      details,
      requestId,
    })
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const apiClient = {
  getHealth: () => request<HealthResponse>('/health'),
  getLive: () => request<HealthResponse>('/health/live'),
  getReady: () => request<HealthResponse>('/health/ready'),
  getFeatures: () => request<FeaturesResponse>('/system/features'),
  getMe: (accessToken: string) =>
    request<MeResponse>('/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  getWorkspace: (role: RoleCode, accessToken: string) =>
    request<WorkspaceResponse>(`/iam/workspaces/${role}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  getPolicies: (params: { page?: number; pageSize?: number; query?: string }, accessToken: string) => {
    const search = new URLSearchParams()
    if (params.page) search.set('page', String(params.page))
    if (params.pageSize) search.set('page_size', String(params.pageSize))
    if (params.query) search.set('q', params.query)
    return request<PageResponse<PolicyListItem>>(`/policies?${search.toString()}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
  },
  getPolicy: (id: string, accessToken: string) =>
    request<PolicyDetail>(`/policies/${encodeURIComponent(id)}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  getHistoricalQa: (params: { page?: number; pageSize?: number; query?: string }, accessToken: string) => {
    const search = new URLSearchParams()
    if (params.page) search.set('page', String(params.page))
    if (params.pageSize) search.set('page_size', String(params.pageSize))
    if (params.query) search.set('q', params.query)
    return request<PageResponse<HistoricalQaListItem>>(`/qa?${search.toString()}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
  },
  getHistoricalQaDetail: (id: string, accessToken: string) =>
    request<HistoricalQaDetail>(`/qa/${encodeURIComponent(id)}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  classify: (text: string, accessToken: string) =>
    request<ClassificationResponse>('/classifications', {
      method: 'POST',
      body: JSON.stringify({ text }),
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  answerPolicyQuestion: (question: string, accessToken: string) =>
    request<PolicyAnswerResponse>('/policy-answers', {
      method: 'POST',
      body: JSON.stringify({ question }),
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  getConsultationDepartments: (accessToken: string) =>
    request<ConsultationDepartment[]>('/consultations/departments', {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  getConsultations: (accessToken: string) =>
    request<ConsultationRecord[]>('/consultations', {
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  createConsultation: (payload: { question: string; selectedDepartmentId: string }, accessToken: string) =>
    request<ConsultationRecord>('/consultations', {
      method: 'POST',
      body: JSON.stringify({ question: payload.question, selected_department_id: payload.selectedDepartmentId }),
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
  replyToConsultation: (id: string, payload: { answer: string; publishToHistory: boolean; publicQuestion?: string; publicAnswer?: string }, accessToken: string) =>
    request<ConsultationRecord>(`/consultations/${encodeURIComponent(id)}/reply`, {
      method: 'POST',
      body: JSON.stringify({
        answer: payload.answer,
        publish_to_history: payload.publishToHistory,
        ...(payload.publicQuestion ? { public_question: payload.publicQuestion } : {}),
        ...(payload.publicAnswer ? { public_answer: payload.publicAnswer } : {}),
      }),
      headers: { Authorization: `Bearer ${accessToken}` },
    }),
}
