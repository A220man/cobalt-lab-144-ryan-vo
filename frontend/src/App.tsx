import { useState, useEffect } from 'react'

interface Item {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

const API_BASE = '/api/v1'

function App() {
  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const fetchItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/items`)
      if (!res.ok) throw new Error('Failed to fetch items')
      const data = await res.json()
      setItems(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const createItem = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      })
      if (!res.ok) throw new Error('Failed to create item')
      await fetchItems()
      setName('')
      setDescription('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchItems()
  }, [])

  return (
    <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Cobalt Lab - Items</h1>

      <form onSubmit={createItem} style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Item name"
          required
          style={{ padding: '0.5rem', fontSize: '1rem' }}
        />
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional)"
          style={{ padding: '0.5rem', fontSize: '1rem' }}
        />
        <button type="submit" disabled={loading || !name.trim()} style={{ padding: '0.5rem', fontSize: '1rem' }}>
          {loading ? 'Creating...' : 'Create Item'}
        </button>
      </form>

      {error && <div style={{ color: 'red', marginBottom: '1rem' }}>Error: {error}</div>}

      <div>
        <h2>Items ({items.length})</h2>
        {loading && <div>Loading...</div>}
        {!loading && items.length === 0 && <div>No items yet. Create one above!</div>}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {items.map((item) => (
            <li key={item.id} style={{ border: '1px solid #ccc', padding: '1rem', marginBottom: '0.5rem', borderRadius: '4px' }}>
              <strong>{item.name}</strong>
              {item.description && <p style={{ margin: '0.5rem 0 0', color: '#666' }}>{item.description}</p>}
              <small style={{ color: '#999' }}>Created: {new Date(item.created_at).toLocaleString()}</small>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default App
