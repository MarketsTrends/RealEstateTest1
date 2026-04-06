import type { AnalysisRequest, AnalysisResponse, ApiError } from './types'

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
