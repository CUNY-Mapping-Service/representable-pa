import { ref, computed, markRaw, type Ref } from "vue";
import { defineStore } from "pinia";
import { Map as MaplibreMap } from "maplibre-gl";

export const useMapStore = defineStore("map", () => {
    const map: Ref<MaplibreMap | undefined> = ref();
    const selectedTracts: Ref<string[]> = ref([]);

    function setMap(mapInstance: MaplibreMap) {
        map.value = markRaw(mapInstance);
    }

    return { map, selectedTracts, setMap }

})

