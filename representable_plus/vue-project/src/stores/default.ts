import { ref, computed, markRaw, type Ref } from 'vue'
import { defineStore } from 'pinia'
import { Map as MaplibreMap } from 'maplibre-gl'

export const useDefaultStore = defineStore('map', () => {
  const map: Ref<MaplibreMap | undefined> = ref()
  const selectedTracts: Ref<string[]> = ref([])
  const mode: Ref<string> = ref('view')
  const choroplethMetric: Ref<string | null> = ref(null)

  function setMode(newMode: string) {
    mode.value = newMode

    switch (newMode) {
      case 'view':
        break
      default:
        break
    }
  }

  function setMap(mapInstance: MaplibreMap) {
    map.value = markRaw(mapInstance)
  }

  function setSelectedTracts(tracts: string[]) {
    selectedTracts.value = tracts
  }

  function setChoroplethMetric(metric: null | string){
    choroplethMetric.value = metric
  }

  return { map, selectedTracts, setSelectedTracts, setChoroplethMetric, setMap, setMode, mode, choroplethMetric }
})
