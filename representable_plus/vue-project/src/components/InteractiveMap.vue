<script setup lang="ts">
import { AttributionControl, Map as MaplibreMap, NavigationControl, Popup } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css'
import { onMounted, ref, toRaw, watch } from 'vue';
import STYLE from '@/stores/default_style';
import { storeToRefs } from 'pinia';
import { useDefaultStore } from '@/stores/default';
import type { TurfWithColors } from '@/views/Landing.vue';
import bbox from '@turf/bbox';

const props = defineProps<{
    turfs: TurfWithColors[],
    selectedTurf: TurfWithColors | null
}>()

const GEOID_FIELD = 'GEOID' // must match the promoteId
const mapCenter = ref<[number, number]>([-75.2038894, 39.962347])
const mapZoom = ref<number>(10.5)
const defaultStore = useDefaultStore()
const { map, selectedTracts, mode } = storeToRefs(defaultStore)

const isMapReady = ref(false);
const editMode = ref<'draw' | 'erase'>('draw');


let hoveredTractIds: string[] = [];
const selectionHistory = ref<string[][]>([]);
const selectionRadius = ref<number>(1);

let currentPopup: Popup | null = null;

// --- when mode changes handle swapping of layers
watch(mode, (newMode) => {
    applyModeSettings(newMode);
})

// --- when turfs and selectedTurf
watch([
    () => props.turfs,
    () => props.selectedTurf,
    map
], () => {
    if (!map.value || !isMapReady.value) return;

    // Close any open popups
    if (currentPopup) {
        currentPopup.remove();
        currentPopup = null;
    }

    const featureCollection = {
        "type": "FeatureCollection",
        "features": props.turfs.map((d) => {
            return {
                type: "Feature",
                properties: {
                    name: d.name,
                    id: d.id,
                    color: d.fillColor,
                    outlineColor: d.outlineColor
                },
                geometry: d.geometry
            };
        })
    }

    // @ts-expect-error setData does not exist
    map.value.getSource('turfs')?.setData(featureCollection);

    // Clear all feature states first
    clearAllFeatureStates();


    if (mode.value === 'view' && !props.selectedTurf) {
        map.value.setFilter('turf-layer', null);
    } else if (mode.value === 'view' && props.selectedTurf) {
        map.value.setFilter('turf-layer', ['==', ['get', 'id'], props.selectedTurf.id]);
    } else if (mode.value === 'suggestion' && props.selectedTurf) {
        map.value.setFilter('turf-layer', ['==', ['get', 'id'], props.selectedTurf.id]);
        selectedTracts.value.forEach(tractId => {
            map.value!.setFeatureState(
                { source: 'tracts', sourceLayer: 'tracts_2023', id: tractId },
                { selected: true }
            );
        });
    } else if (mode.value === 'edit') {
        selectedTracts.value.forEach(tractId => {
            map.value!.setFeatureState(
                { source: 'tracts', sourceLayer: 'tracts_2023', id: tractId },
                { selected: true }
            );
        });
    }

    // zoom to selectedTurf, otherwise turfs
    let targetFeatureCollection: any = null;

    if (props.selectedTurf) {
        targetFeatureCollection = {
            type: "FeatureCollection",
            features: [{
                type: "Feature",
                properties: {},
                geometry: props.selectedTurf.geometry
            }]
        };
    } else if (props.turfs.length > 0) {
        targetFeatureCollection = featureCollection;
    }

    if (targetFeatureCollection) {
        const [minX, minY, maxX, maxY] = bbox(targetFeatureCollection);
        map.value.fitBounds(
            [[minX, minY], [maxX, maxY]],
            { padding: 40, animate: false, maxZoom: 14 }
        );
    }

}, { deep: true });

function clearAllFeatureStates() {
    if (!map.value || !isMapReady.value) return;
    map.value.removeFeatureState({ source: 'tracts', sourceLayer: 'tracts_2023' });
}

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
        defaultStore.setMap(mapInstance);

        //setupEditModeInteraction();
        setupViewModeInteraction();
        applyModeSettings(mode.value);
    });
})

function updateTractColors() {

}

function applyModeSettings(newMode: string) {
    if (!map.value || !isMapReady.value) return;

    // Close any open popups when switching modes
    if (currentPopup) {
        currentPopup.remove();
        currentPopup = null;
    }

    selectionHistory.value = []

    switch (newMode) {
        case 'edit':
            // set the selected tracts
            selectedTracts.value = props.selectedTurf?.tracts ?? []
            map.value.setLayoutProperty("turf-layer", "visibility", 'none');
            map.value.setLayoutProperty("tract-layer", "visibility", 'visible');
            map.value.setLayoutProperty("tract-hover-layer", "visibility", 'visible');
            updateTractColors();
            break
        case 'view':
            map.value.setLayoutProperty("turf-layer", "visibility", 'visible');
            map.value.setLayoutProperty("tract-layer", 'visibility', 'none');
            map.value.setLayoutProperty("tract-hover-layer", 'visibility', 'none');
            updateTractColors()
            break
        case 'suggestion':
            map.value.setLayoutProperty("turf-layer", "visibility", 'visible');
            map.value.setLayoutProperty("tract-layer", 'visibility', 'visible');
            map.value.setLayoutProperty("tract-hover-layer", 'visibility', 'none');
            updateTractColors()
            break
        default:
            map.value.setLayoutProperty("turf-layer", "visibility", 'visible');
            map.value.setLayoutProperty("tract-layer", 'visibility', 'none');
            map.value.setLayoutProperty("tract-hover-layer", 'visibility', 'none');
    }
}

function setupViewModeInteraction() {
    /* Popup interactions for view mode */
    if (!map.value) return;

    const handleViewClick = (e: any) => {
        if (!map.value || mode.value !== 'view') return;

        const features = map.value.queryRenderedFeatures(e.point, {
            layers: ['tract-layer', 'turf-layer']
        });

        // Close existing popup
        if (currentPopup) currentPopup.remove();

        if (features.length > 0) {
            const names = features.filter(d => d.layer.id === 'turf-layer').map(d => d.properties.name)
            // const tractId = features.find(d => d.layer.id === 'tract-layer')?.properties.tract


            // Create popup content
            const popupContent = `
                <div style="padding: 4px;">
                    <div style="margin-top: 2px;">
                        ${names.map(name => `<div style="font-size: 0.85rem; padding: 2px 0;">• ${name}</div>`).join('')}
                    </div>
                </div>
            `;

            currentPopup = new Popup({ closeButton: true, closeOnClick: false })
                .setLngLat(e.lngLat)
                .setHTML(popupContent)
                .addTo(map.value);
        }

    };

    const handleViewHover = (e: any) => {
        if (!map.value || mode.value !== 'view') return;
        map.value.getCanvas().style.cursor = 'pointer';
    };

    const handleViewLeave = () => {
        if (!map.value) return;
        map.value.getCanvas().style.cursor = '';
    };

    map.value.on('click', handleViewClick);
    map.value.on('mouseenter', handleViewHover);
    map.value.on('mouseleave', handleViewLeave);
}


</script>

<template>
    <div id="map" class="map"></div>
</template>

<style scoped>
#map {
    width: 100%;
    height: 100%;
}
</style>
