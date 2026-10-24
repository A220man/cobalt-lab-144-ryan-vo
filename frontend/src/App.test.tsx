import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import App from './App'

describe('App', () => {
  beforeEach(() => {
    // fetch is mocked in vitest.setup.ts
    vi.mocked(fetch).mockReset()
    cleanup()
  })

  it('renders the title', () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })
    render(<App />)
    expect(screen.getByText('Cobalt Lab - Items')).toBeInTheDocument()
  })

  it('shows empty state when no items', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    })
    render(<App />)
    await waitFor(() => {
      const elements = screen.getAllByText('No items yet. Create one above!')
      expect(elements.length).toBeGreaterThan(0)
      expect(elements[0]).toBeInTheDocument()
    })
  })

  it('displays items when they exist', async () => {
    const mockItems = [
      { id: 1, name: 'Test Item', description: 'A test', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ]
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockItems,
    })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Test Item')).toBeInTheDocument()
    })
  })
})
