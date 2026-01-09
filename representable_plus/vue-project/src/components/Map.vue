<script setup lang="ts">
import { useMapStore } from '@/stores/map';
import { useTurfStore } from '@/stores/turf';
import { AttributionControl, Map as MaplibreMap, NavigationControl, Popup } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, ref, watch } from 'vue';
import STYLE from '@/stores/default_style';
import { storeToRefs } from 'pinia';

const GEOID_FIELD = 'geoid' // must match the promoteId
const mapCenter = ref<[number, number]>([-73.9769, 40.72103])
const mapZoom = ref<number>(10.5)
const mapStore = useMapStore()
const turfStore = useTurfStore()
const { map, selectedTracts } = storeToRefs(mapStore)
const { selectedTurf, turfs } = storeToRefs(turfStore)

const isMapReady = ref(false);

onMounted(() => {
    const mapInstance = new MaplibreMap({
        container: "map",
        // @ts-expect-error property in style are incompatible with MapOptions
        style: STYLE,
        center: mapCenter.value,
        zoom: mapZoom.value,
        attributionControl: false
    });

    mapInstance.on('load', () => {
        isMapReady.value = true;
        mapStore.setMap(mapInstance);


    });
})

</script>

<template>
    <div id="map" class="map"></div>
</template>

<style scoped>
#map {
    width: 100%;
    height: 100%;
}

.map-container {
    position: relative;
    flex: 1;
    order: -1;
    z-index: 9;
}
</style>