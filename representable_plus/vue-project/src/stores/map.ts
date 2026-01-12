import { ref, computed, markRaw, type Ref } from 'vue'
import { defineStore } from 'pinia'
import { Map as MaplibreMap } from 'maplibre-gl'

export const useMapStore = defineStore('map', () => {
  const map: Ref<MaplibreMap | undefined> = ref()
  const selectedTracts: Ref<string[]> = ref([])
  const mode: Ref<string> = ref('view')

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

  return { map, selectedTracts, setMap, setMode, mode }
})
