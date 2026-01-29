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

        setupEditModeInteraction();
        setupViewModeInteraction();

        applyModeSettings(mode.value);
    });
})

// Watch for changes in selectedTracts and turfs to update colors
watch([selectedTracts, () => props.turfs, () => props.selectedTurf, mode], () => {
    updateTractColors();
}, { deep: true });

// Watch for selectedTurf changes to zoom to it
watch(() => props.selectedTurf, (newTurf) => {
    if (!map.value || !isMapReady.value || !newTurf) return;

    if (
        newTurf.min_lon !== undefined &&
        newTurf.min_lat !== undefined &&
        newTurf.max_lon !== undefined &&
        newTurf.max_lat !== undefined
    ) {
        map.value.fitBounds(
            [
                [newTurf.min_lon, newTurf.min_lat],
                [newTurf.max_lon, newTurf.max_lat]
            ],
            {
                padding: 50,
                duration: 1000,
                maxZoom: 13
            }
        );
    }
});

// Watch for mode changes to apply mode settings
watch(mode, (newMode) => {
    applyModeSettings(newMode);
})

function clearAllFeatureStates() {
    if (!map.value || !isMapReady.value) return;
    map.value.removeFeatureState({ source: 'tracts', sourceLayer: 'tracts_2023' });
}

function applyModeSettings(newMode: string) {
    if (!map.value || !isMapReady.value) return;

    // Close any open popups when switching modes
    if (currentPopup) {
        currentPopup.remove();
        currentPopup = null;
    }

    selectionHistory.value = []
    map.value.setLayoutProperty('tract-choropleth', 'visibility', 'none');
    switch (newMode) {

        case 'edit':
            // set the selected tracts
            selectedTracts.value = props.selectedTurf?.tracts ?? []
            map.value.setLayoutProperty("turf-layer", "visibility", props.selectedTurf ? 'visible' : 'none');
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
    map.value.on('mouseenter', 'turf-layer', handleViewHover);
    map.value.on('mouseleave', 'turf-layer', handleViewLeave);
}

function setupEditModeInteraction() {
    /* mouse events for editing  */
    if (!map.value) return;

    // Hover effect with preview
    const handleMouseMove = (e: any) => {
        if (!map.value || mode.value !== 'edit') return;

        map.value.getCanvas().style.cursor = 'pointer';

        // Get nearby tracts based on selection radius
        const nearbyTracts = getNearbyTracts(e.lngLat, selectionRadius.value);
        updateHoverPreview(nearbyTracts);
    };

    const handleMouseLeave = () => {
        if (!map.value) return;

        map.value.getCanvas().style.cursor = '';
        updateHoverPreview([]);
    };

    map.value.on('mousemove', 'tract-hover-layer', handleMouseMove);
    map.value.on('mouseleave', 'tract-hover-layer', handleMouseLeave);

    // Click to select/deselect - listen on both layers
    const handleClick = (e: any) => {
        if (!map.value || mode.value !== 'edit') return;

        e.preventDefault();

        const tractsToModify = getNearbyTracts(e.lngLat, selectionRadius.value);

        if (tractsToModify.length > 0) {
            // Save current state to history
            selectionHistory.value.push([...selectedTracts.value]);

            if (editMode.value === 'draw') {
                // Add tracts (avoid duplicates)
                const newTracts = tractsToModify.filter(id => !selectedTracts.value.includes(id));
                selectedTracts.value = [...selectedTracts.value, ...newTracts];
            } else {
                // Erase tracts
                selectedTracts.value = selectedTracts.value.filter(id => !tractsToModify.includes(id));
            }

            updateTractColors();
        }
    };

    map.value.on('click', 'tract-hover-layer', handleClick);
}

function undo() {
    if (selectionHistory.value.length > 0) {
        selectedTracts.value = selectionHistory.value.pop() || [];
        updateTractColors();
    }
}

function updateTractColors() {
    if (!map.value || !isMapReady.value) return;

    const featureCollection = {
        "type": "FeatureCollection",
        "features": toRaw(props.turfs).map((d) => {
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
    } else if (mode.value === 'edit' && props.selectedTurf) {
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
}

function getNearbyTracts(centerLngLat: any, radius: number): string[] {
    /* Allows a user to select more than one tract based on the radius slider */
    if (!map.value) return [];

    try {
        const centerPoint = map.value.project(centerLngLat);

        // Calculate pixel radius and get bbox
        const pixelRadius = radius * 6;
        const bbox: [[number, number], [number, number]] = [
            [centerPoint.x - pixelRadius, centerPoint.y - pixelRadius],
            [centerPoint.x + pixelRadius, centerPoint.y + pixelRadius]
        ];

        // Query rendered features in the bounding box
        const features = map.value.queryRenderedFeatures(bbox, {
            layers: ['tract-layer']
        });

        const tractIds = features.map(f => f.properties?.[GEOID_FIELD]).filter(Boolean);

        return tractIds as string[];
    } catch (error) {
        return [];
    }
}

function updateHoverPreview(tractIds: string[]) {
    if (!map.value || !isMapReady.value) return;

    // Clear hover state from previously hovered tracts
    hoveredTractIds.forEach(tractId => {
        map.value!.setFeatureState(
            { source: 'tracts', sourceLayer: 'tracts_2023', id: tractId },
            { hover: false }
        );
    });

    tractIds.forEach(tractId => {
        map.value!.setFeatureState(
            { source: 'tracts', sourceLayer: 'tracts_2023', id: tractId },
            { hover: true }
        );
    });

    hoveredTractIds = tractIds;
}
</script>

<template>
    <div id="map" class="map">
        <!-- Edit mode controls -->
        <div v-if="mode === 'edit'" class="edit-controls box px-2 py-3">
            <div v-if="selectedTurf" class="notification is-info is-light py-2 px-3 mb-3">
                <p class="is-size-7"><strong>Editing:</strong> {{ selectedTurf.name }}</p>
            </div>

            <div class="field">
                <div class="control">
                    <div class="buttons has-addons">
                        <button class="button px-3 py-1" :class="{ 'is-info is-selected': editMode === 'draw' }"
                            @click="editMode = 'draw'">
                            <span class="icon">
                                ✏️
                            </span>
                            <span>Draw</span>
                        </button>
                        <button class="button px-3 py-1" :class="{ 'is-danger is-selected': editMode === 'erase' }"
                            @click="editMode = 'erase'">
                            <span class="icon">
                                🧽
                            </span>
                            <span>Erase</span>
                        </button>
                    </div>
                </div>
            </div>

            <div class="field">
                <label class="label mb-0">Selection Size: {{ selectionRadius }}</label>
                <div class="control">
                    <input id="selection-radius" type="range" v-model.number="selectionRadius" min="1" max="10" step="1"
                        class="slider is-fullwidth is-info" />
                </div>
            </div>

            <div class="field">
                <div class="control">
                    <button @click="undo" :disabled="selectionHistory.length === 0"
                        class="button is-info is-fullwidth py-1">
                        <span class="icon">↩️</span>
                        <span>Undo ({{ selectionHistory.length }})</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
#map {
    width: 100%;
    height: 100%;
}

.edit-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 10;
}

.slider {
    appearance: none;
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: #dbdbdb;
    outline: none;
}

.buttons.has-addons .button.is-selected {
    z-index: 2;
}
</style>