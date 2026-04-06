import type { AnalysisRequest, AnalysisResponse, ApiError, CompsResponse } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function parseApiError(errorBody: ApiError, fallbackStatus: number): Error {
  if (Array.isArray(errorBody.detail)) {
    const messages = errorBody.detail.map((e) => e.msg).filter(Boolean).join('; ')
    return new Error(messages || 'Validation error')
  }
  return new Error(errorBody.detail || `Request failed (${fallbackStatus})`)
}

export async function postAnalysis(payload: AnalysisRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as ApiError
    throw parseApiError(errorBody, response.status)
  }

  return (await response.json()) as AnalysisResponse
}

export async function downloadPdfReport(payload: AnalysisRequest): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/report/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as ApiError
    throw parseApiError(errorBody, response.status)
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'deal-analysis-report.pdf'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export async function getCompsSales(params: {
  lat: number
  lon: number
  radius_m?: number
  months_back?: number
  property_type?: string
  surface_m2?: number
  surface_tolerance_pct?: number
}): Promise<CompsResponse> {
  const query = new URLSearchParams({
    lat: String(params.lat),
    lon: String(params.lon),
    radius_m: String(params.radius_m ?? 1000),
    months_back: String(params.months_back ?? 24),
    property_type: params.property_type ?? 'unknown'
  })

  if (params.surface_m2 !== undefined) {
    query.set('surface_m2', String(params.surface_m2))
  }
  if (params.surface_tolerance_pct !== undefined) {
    query.set('surface_tolerance_pct', String(params.surface_tolerance_pct))
  }

  const response = await fetch(`${API_BASE_URL}/comps/sales?${query.toString()}`)
  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as ApiError
    throw parseApiError(errorBody, response.status)
  }
  return (await response.json()) as CompsResponse
}
