const BASE_URL = '/api/v1'

export class ApiError extends Error {
  code?: string
  status: number
  details?: any

  constructor(message: string, status: number, code?: string, details?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp('(^|;\\s*)csrf_token=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

export async function request<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`
  const headers = new Headers(options.headers || {})

  // Set CSRF token for mutating methods
  const method = (options.method || 'GET').toUpperCase()
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken()
    if (csrf && !headers.has('x-csrf-token')) {
      headers.set('x-csrf-token', csrf)
    }
  }

  // Auto set Content-Type to JSON if sending raw object and not already FormData
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  })

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  const contentType = response.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')

  let data: any
  try {
    data = isJson ? await response.json() : await response.text()
  } catch (err) {
    data = null
  }

  if (!response.ok) {
    const message =
      (data && (data.message || data.detail)) ||
      response.statusText ||
      `Request failed with status ${response.status}`
    const code = data && data.code
    throw new ApiError(message, response.status, code, data)
  }

  return data as T
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: any, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body?: any, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),

  upload: <T>(endpoint: string, formData: FormData, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    }),
}

