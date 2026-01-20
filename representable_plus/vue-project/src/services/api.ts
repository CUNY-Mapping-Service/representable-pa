const getBaseRoute = () => {
  return window.location.pathname === '/' ? 'http://127.0.0.1:8000/partners/test/turf/api' : './api'
}

export const demographicsApi = {
  async getByRecordId(recordId: number) {
    const response = await fetch(`${getBaseRoute()}/demographics?record_id=${recordId}`, {
      method: 'GET'
    })
    if (!response.ok) throw new Error('Failed to fetch demographics')
    return response.json()
  },

  async getByTracts(tracts: string[]) {
    const response = await fetch(`${getBaseRoute()}/demographics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tracts }),
    })
    if (!response.ok) throw new Error('Failed to fetch demographics')
    return response.json()
  },
}
