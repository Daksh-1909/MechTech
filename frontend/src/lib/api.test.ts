import { afterEach, describe, expect, it, vi } from 'vitest'

import { request } from './api'

afterEach(() => {
  document.cookie = 'mechtech_csrf=; Max-Age=0; path=/'
  vi.unstubAllGlobals()
})

describe('API client', () => {
  it('sends the backend CSRF cookie value on mutating requests', async () => {
    document.cookie = 'mechtech_csrf=csrf-token; path=/'
    const fetchMock = vi.fn<typeof fetch>(
      async (_input, _init) => new Response(null, { status: 204 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await request('/auth/logout', { method: 'POST' })

    const [, options] = fetchMock.mock.calls[0]
    expect(options?.headers).toBeInstanceOf(Headers)
    expect(new Headers(options?.headers).get('x-csrf-token')).toBe('csrf-token')
  })
})
