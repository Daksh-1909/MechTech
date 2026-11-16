import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const user = {
  id: 'user-1',
  display_name: 'Demo Admin',
  email: 'demo.admin@example.com',
  status: 'active',
  is_active: true,
  roles: ['platform_admin'],
  permissions: [],
  organizations: [],
  created_at: '2026-11-16T00:00:00Z',
  updated_at: '2026-11-16T00:00:00Z',
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockUnauthenticatedFetch() {
  const fetchMock = vi.fn(async () =>
    jsonResponse({ error: { message: 'Authentication required.', code: 'UNAUTHORIZED' } }, 401),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
})

describe('App routing and authentication', () => {
  it('shows the public landing page before authentication', async () => {
    mockUnauthenticatedFetch()

    render(<App />)

    expect(
      screen.getByRole('heading', { name: /keep critical equipment in view/i }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /request an account/i })).toHaveAttribute(
      'href',
      '/register',
    )
  })

  it('restores an existing session from the bare /auth/me user response', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(user))
    vi.stubGlobal('fetch', fetchMock)
    window.history.replaceState({}, '', '/equipment')

    render(<App />)

    expect(await screen.findByText('Demo Admin')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Equipment Fleet' })).toBeInTheDocument()
  })

  it('redirects workspace routes to sign-in and returns to the requested page after login', async () => {
    window.history.replaceState({}, '', '/alerts')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) {
        return jsonResponse(
          { error: { message: 'Authentication required.', code: 'UNAUTHORIZED' } },
          401,
        )
      }
      if (url.endsWith('/auth/login')) {
        expect(JSON.parse(String(init?.body))).toEqual({
          email: user.email,
          password: 'demo-password-123',
        })
        return jsonResponse({ user, csrf_token: 'csrf-token', expires_at: user.updated_at })
      }
      return jsonResponse([])
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await screen.findByRole('heading', { name: /sign in to mechtech/i })
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), {
      target: { value: user.email },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••••••'), {
      target: { value: 'demo-password-123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(window.location.pathname).toBe('/alerts'))
    expect(await screen.findByText('Admin & Auditing')).toBeInTheDocument()
  })

  it('shows the backend error message instead of the generic HTTP status text', async () => {
    window.history.replaceState({}, '', '/login')
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/me')) {
        return jsonResponse(
          { error: { message: 'Authentication required.', code: 'UNAUTHORIZED' } },
          401,
        )
      }
      return jsonResponse(
        { error: { message: 'Invalid email or password.', code: 'INVALID_CREDENTIALS' } },
        401,
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await screen.findByRole('heading', { name: /sign in to mechtech/i })
    fireEvent.change(screen.getByPlaceholderText('name@example.com'), {
      target: { value: 'unknown@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText('••••••••••••'), {
      target: { value: 'wrong-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Invalid email or password.')).toBeInTheDocument()
    expect(screen.queryByText('Bad Request')).not.toBeInTheDocument()
  })
})
