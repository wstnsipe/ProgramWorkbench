/**
 * Base HTTP client.
 * All API functions import from here — no raw fetch() calls in components.
 */

const BASE = import.meta.env.VITE_API_BASE_URL as string

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly body: unknown = null,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let detail = `HTTP ${res.status}`
  let body: unknown = null
  try {
    body = await res.json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const d = (body as Record<string, unknown>).detail
      detail = typeof d === 'string' ? d : JSON.stringify(d)
    }
  } catch {
    // body was not JSON
  }
  return new ApiError(res.status, detail, body)
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init.headers },
    ...init,
  })
  if (!res.ok) throw await parseError(res)
  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return apiFetch<T>(path)
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'PUT',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'PATCH',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export function apiDelete(path: string): Promise<void> {
  return apiFetch<void>(path, { method: 'DELETE' })
}

/** Multipart upload — does NOT set Content-Type (browser sets boundary automatically) */
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const url = `${BASE}${path}`
  const res = await fetch(url, { method: 'POST', body: formData })
  if (!res.ok) throw await parseError(res)
  return res.json() as Promise<T>
}

/** Build a download URL (used for document download links) */
export function apiDownloadUrl(path: string): string {
  return `${BASE}${path}`
}
