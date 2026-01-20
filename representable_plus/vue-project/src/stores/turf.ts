import { demographicsApi } from '@/services/api'
import type { GeoJSONFeature } from 'maplibre-gl'
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

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

export const useTurfStore = defineStore('turf', () => {
  const turfs = ref<Turf[]>([])
  const selectedTurf = ref<Turf | null>(null)

  const route = useRoute()
  const API_BASE_ROUTE =
    route.path === '/' ? 'http://127.0.0.1:8000/partners/test/turf/api' : './api'

  const demographics = ref<DemographicsResponse | null>(null)
  const loadingDemographics = ref(false)
  const demographicsError = ref<string | null>(null)

  const suggestions = ref<TractSuggestion[]>([])

  async function loadTurfs() {
    fetch(API_BASE_ROUTE + '/edit')
      .then((res) => res.json())
      .then((data) => {
        turfs.value = data.map((row: any) => {
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
      .catch((error) => console.error('Error loading turfs from api:', error))
  }

  const sortedTurfs = computed(() => {
    return [...turfs.value].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    )
  })

  // -- selection
  // Select a turf
  function selectTurf(turf: Turf | null) {
    selectedTurf.value = turf
  }

  // Clear selected turf
  function clearSelectedTurf() {
    selectedTurf.value = null
  }

  // -- CRUD calls

  async function addTurf(turfData: { name: string; details: string; tracts: string[] }) {
    try {
      const response = await fetch(API_BASE_ROUTE + '/edit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tracts: turfData.tracts,
          description: {
            name: turfData.name,
            details: turfData.details,
          },
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create turf')
      }

      const newRecord = await response.json()

      // Add the new turf to the local state
      const newTurf: Turf = {
        id: newRecord.id,
        name: newRecord.description.name || '',
        details: newRecord.description.details || '',
        createdAt: newRecord.description.createdAt,
        tracts: newRecord.tracts,
      }

      turfs.value.push(newTurf)
      selectedTurf.value = newTurf

      return newTurf
    } catch (error) {
      console.error('Error adding turf:', error)
      throw error
    }
  }

  async function updateTurf(
    id: number,
    turfData: { name: string; details: string; tracts: string[] },
  ) {
    try {
      const response = await fetch(API_BASE_ROUTE + '/edit', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: id,
          tracts: turfData.tracts,
          description: {
            name: turfData.name,
            details: turfData.details,
          },
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to update turf')
      }

      const updatedRecord = await response.json()

      // Update the turf in local state
      const index = turfs.value.findIndex((t) => t.id === id)
      if (index !== -1) {
        turfs.value[index] = {
          id: updatedRecord.id,
          name: updatedRecord.description.name || '',
          details: updatedRecord.description.details || '',
          createdAt: updatedRecord.description.createdAt,
          tracts: updatedRecord.tracts,
        }
        selectedTurf.value = turfs.value[index]
      }

      return turfs.value[index]
    } catch (error) {
      console.error('Error updating turf:', error)
      throw error
    }
  }

  async function deleteTurf(id: number) {
    try {
      const response = await fetch(API_BASE_ROUTE + `/edit?id=${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete turf')
      }

      // Remove the turf from local state
      turfs.value = turfs.value.filter((t) => t.id !== id)

      // Clear selection if the deleted turf was selected
      if (selectedTurf.value?.id === id) {
        selectedTurf.value = null
      }

      return true
    } catch (error) {
      console.error('Error deleting turf:', error)
      throw error
    }
  }

  async function fetchDemographics() {
    if (!selectedTurf.value?.tracts || selectedTurf.value.tracts.length === 0) {
      demographics.value = null
      return
    }

    loadingDemographics.value = true
    demographicsError.value = null

    try {
      // Use record_id if available, otherwise use tracts array
      const data = selectedTurf.value.id
        ? await demographicsApi.getByRecordId(selectedTurf.value.id)
        : await demographicsApi.getByTracts(selectedTurf.value.tracts)

      demographics.value = data
    } catch (error) {
      console.error('Failed to fetch demographics:', error)
      demographicsError.value = 'Failed to load demographic data'
      demographics.value = null
    } finally {
      loadingDemographics.value = false
    }
  }

  async function fetchSuggestions() {
    if (selectedTurf.value?.id){
       fetch(API_BASE_ROUTE + '/suggestions/' + selectedTurf.value?.id)
      .then((res) => res.json())
      .then((data) => suggestions.value = data.suggestions)
    }
    return []
  }

  watch(selectedTurf, (newTurf) => {
    if (newTurf) {
      fetchDemographics()
      fetchSuggestions()
    } else {
      demographics.value = null
      suggestions.value = []
    }
  })

  return {
    turfs,
    sortedTurfs,
    selectedTurf,
    loadTurfs,
    selectTurf,
    clearSelectedTurf,
    addTurf,
    updateTurf,
    deleteTurf,
    demographics,
    loadingDemographics,
    demographicsError,
    fetchDemographics,
    fetchSuggestions,
    suggestions
  }
})
