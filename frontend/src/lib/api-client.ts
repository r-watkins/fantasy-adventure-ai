export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `Request failed with status ${status}`)
    this.status = status
    this.detail = detail
  }
}

type JsonBody = Record<string, unknown>

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    // Session auth is an HttpOnly cookie (never localStorage), so every
    // request needs the browser to actually send it - including
    // cross-container calls through the Vite dev proxy.
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const body: unknown = await response.json().catch(() => undefined)

  if (!response.ok) {
    const detail =
      body !== undefined && body !== null && typeof body === 'object' && 'detail' in body
        ? (body as { detail: unknown }).detail
        : body
    throw new ApiError(response.status, detail)
  }

  return body as T
}

// Backend detail strings (e.g. "Invalid email or password", "Email is
// already registered") are already user-appropriate copy - surface them
// as-is. Pydantic validation errors (422) come back as a list, not a
// string, so those fall through to the caller's fallback message.
export function describeApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      return 'Too many attempts. Please wait a moment and try again.'
    }
    if (typeof error.detail === 'string') {
      return error.detail
    }
  }
  return fallback
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: JsonBody) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: JsonBody) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: JsonBody) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
}
