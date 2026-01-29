import type { GeoJSONFeature } from 'maplibre-gl'

export interface Turf {
  id: number
  organization_id?: number | null
  name: string
  details: string
  tracts: string[]
  createdAt: string
  geometry?: GeoJSONFeature
  max_lat?: number
  max_lon?: number
  min_lat?: number
  min_lon?: number
}

export interface DemographicMetrics {
  [key: string]: number | string
}

export interface TractDemographics extends DemographicMetrics {
  geoid: number
  tract: number
  county_name: string
  state_name: string
}

export interface DemographicsResponse {
  aggregated: DemographicMetrics
  by_tract: TractDemographics[]
}

export interface TractSuggestion {
  description: string
  tracts: string[]
  type: string
  id: number
}

export const getBaseRoute = () => {
  return window.location.pathname === '/' ? 'http://127.0.0.1:8000/partners/test/turf/api' : './api'
}

export const demographicsApi = {
  async getByRecordId(recordId: number) {
    const response = await fetch(`${getBaseRoute()}/demographics?record_id=${recordId}`, {
      method: 'GET',
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

export const turfApi = {
  async loadTurfs(): Promise<Turf[]> {
    return await fetch(getBaseRoute() + '/edit')
      .then((res) => res.json())
      .then((data) => {
        return data.map((row: any) => {
          const { id, tracts, geometry, max_lat, max_lon, min_lat, min_lon } = row

          return {
            id,
            tracts,
            geometry,
            max_lat,
            max_lon,
            min_lat,
            min_lon,
            name: row.description.name || '',
            details: row.description.details || '',
            createdAt: row.description.createdAt,
          }
        })
      })
      .catch((error) => {
        console.error('Error loading turfs from api:', error)
        return []
      })
  },

  async fetchDemographics(selectedTurf: Turf) {
    if (!selectedTurf?.tracts || selectedTurf.tracts.length === 0) {
      return null
    }

    try {
      const data = selectedTurf.id
        ? await demographicsApi.getByRecordId(selectedTurf.id)
        : await demographicsApi.getByTracts(selectedTurf.tracts)

      return data
    } catch (error) {
      console.error('Failed to fetch demographics:', error)
      return []
    }
  },

  async fetchSuggestions(selectedTurf: Turf) {
    if (selectedTurf.id) {
      return await fetch(getBaseRoute() + '/suggestions/' + selectedTurf.id)
        .then((res) => res.json())
        .then((data) => data?.suggestions ?? [])
        .catch((error) => {
          console.error('Failed to fetch suggestions:', error)
          return []
        })
    }
  },
}
