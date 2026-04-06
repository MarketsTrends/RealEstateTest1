import type { AnalysisRequest, AnalysisResponse, ApiError } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function postAnalysis(payload: AnalysisRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as ApiError
    if (Array.isArray(errorBody.detail)) {
      const messages = errorBody.detail.map((e) => e.msg).filter(Boolean).join('; ')
      throw new Error(messages || 'Validation error')
    }
    throw new Error(errorBody.detail || `Request failed (${response.status})`)
  }

  return (await response.json()) as AnalysisResponse
}
