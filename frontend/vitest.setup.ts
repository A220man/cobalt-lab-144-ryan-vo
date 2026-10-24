import { vi, expect, beforeEach } from 'vitest'
globalThis.expect = expect

// Dynamic import to ensure expect is set before jest-dom tries to extend it
import('@testing-library/jest-dom')

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Reset mocks before each test
beforeEach(() => {
  mockFetch.mockReset()
})
