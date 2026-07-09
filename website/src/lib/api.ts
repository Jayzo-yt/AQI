export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || ''

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${path}`)
  }
  return response.json() as Promise<T>
}
