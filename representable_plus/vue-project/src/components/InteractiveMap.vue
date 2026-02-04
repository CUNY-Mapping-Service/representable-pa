<script setup lang="ts">
import { Map as MaplibreMap, Marker, NavigationControl, Popup } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css'
import { computed, onMounted, ref, toRaw, watch } from 'vue';
import STYLE from '@/stores/default_style';
import { storeToRefs } from 'pinia';
import { useDefaultStore } from '@/stores/default';
import type { TurfWithColors } from '@/views/Landing.vue';
import AddressSearch from './AddressSearch.vue';
import DemographicsOverlay from './DemographicsOverlay.vue';
import { getBaseRoute } from '@/services/api';

const MAPBOX_TOKEN = 'pk.eyJ1IjoiY3VueWN1ciIsImEiOiJfQmNSMF9NIn0.uRgbcFeJbw2xyTUZY8gYeA';

const props = defineProps<{
    turfs: TurfWithColors[],
    selectedTurf: TurfWithColors | null
}>()

const emit = defineEmits<{
    save: []
    close: []
}>()

const GEOID_FIELD = 'GEOID' // must match the promoteId
let currentMarker: Marker | null = null;
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

// Form fields
const turfName = ref('')
const turfDetails = ref('')
const showNameDescriptionModal = ref(false)
const showEditFormModal = ref(false)

const isFormValid = computed(() => {
    return turfName.value.trim() !== '' &&
        turfDetails.value.trim() !== '' &&
        selectedTracts.value.length > 0
})

const hasChanges = computed(() => {
    if (!props.selectedTurf) {
        return turfName.value.trim() !== '' ||
            turfDetails.value.trim() !== '' ||
            selectedTracts.value.length > 0
    } else {
        return turfName.value !== props.selectedTurf.name ||
            turfDetails.value !== props.selectedTurf.details ||
            JSON.stringify([...selectedTracts.value].sort()) !==
            JSON.stringify([...props.selectedTurf.tracts].sort())
    }
})

onMounted(() => {
    const mapInstance = new MaplibreMap({
        container: "map",
        // @ts-expect-error property in style are incompatible with MapOptions
        style: STYLE,
        center: mapCenter.value,
        zoom: mapZoom.value,
        attributionControl: false
    });

    // Move navigation controls to bottom-left
    mapInstance.addControl(new NavigationControl(), 'bottom-left');

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

    // Populate form fields when editing existing turf
    turfName.value = newTurf.name ?? ''
    turfDetails.value = newTurf.details ?? ''

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

    // Show modal for new turf creation
    if (newMode === 'edit' && !props.selectedTurf) {
        showNameDescriptionModal.value = true
        turfName.value = ''
        turfDetails.value = ''
    }
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

    const canvas = document.createElement('canvas');
    canvas.width = 32;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    if (ctx) {
        ctx.font = '24px serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('🧽', 16, 16);
    }

    // Hover effect with preview
    const handleMouseMove = (e: any) => {
        if (!map.value || mode.value !== 'edit') return;

        switch (editMode.value) {
            case 'draw':
                map.value.getCanvas().style.cursor = 'cell';
                break;
            case 'erase':
                map.value.getCanvas().style.cursor = `url(${canvas.toDataURL()}), auto`;
                break;
            default:
                map.value.getCanvas().style.cursor = 'pointer';
        }

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

async function handleAddressSearchResult(result: { feature: any; additionalData: any[] }) {
    const { feature } = result;

    if (currentMarker) {
        currentMarker.remove();
        currentMarker = null;
    }

    // Check if feature has a center point
    const center = feature.center || feature.geometry?.coordinates;

    if (center && center.length === 2 && map.value) {
        currentMarker = new Marker()
            .setLngLat([center[0], center[1]])
            .addTo(map.value);

        // move/zoom map to result
        map.value?.flyTo({ center: [center[0], center[1]], zoom: 13 });
    }
}

function closeNameDescriptionModal() {
    if (hasChanges.value) {
        if (!confirm('Are you sure you want to cancel? Your changes will be lost.')) {
            return
        }
    }

    showNameDescriptionModal.value = false
    selectedTracts.value = []
    turfName.value = ''
    turfDetails.value = ''
    emit('close')
}

function proceedToDrawing() {
    if (!turfName.value.trim() || !turfDetails.value.trim()) {
        alert('Please enter both name and description')
        return
    }
    showNameDescriptionModal.value = false
}

function openEditForm() {
    showEditFormModal.value = true
}

function closeEditForm() {
    showEditFormModal.value = false
}

async function saveTurf() {
    if (!isFormValid.value) return

    try {
        const payload = {
            name: turfName.value.trim(),
            details: turfDetails.value.trim(),
            tracts: [...selectedTracts.value]
        }

        let response;
        if (props.selectedTurf) {
            // Update existing turf
            response = await fetch(`${getBaseRoute()}/edit/${props.selectedTurf.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
        } else {
            // Create new turf
            response = await fetch(`${getBaseRoute()}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
        }

        if (!response.ok) {
            throw new Error('Failed to save turf')
        }

        // Emit save event to trigger refresh in parent
        emit('save')

        // Reset form
        turfName.value = ''
        turfDetails.value = ''
        selectedTracts.value = []
        showEditFormModal.value = false

        // Close the editor
        emit('close')
    } catch (error) {
        console.error('Failed to save turf:', error)
        alert('Failed to save turf. Please try again.')
    }
}

async function deleteTurf() {
    if (!props.selectedTurf) return

    const confirmMessage = `Are you sure you want to delete "${props.selectedTurf.name}"? This action cannot be undone.`

    if (confirm(confirmMessage)) {
        try {
            const response = await fetch(`${getBaseRoute()}/edit/${props.selectedTurf.id}`, {
                method: 'DELETE'
            })

            if (!response.ok) {
                throw new Error('Failed to delete turf')
            }

            // Reset state after deletion
            turfName.value = ''
            turfDetails.value = ''
            selectedTracts.value = []

            // Emit save to trigger refresh and close
            emit('save')
            emit('close')
        } catch (error) {
            console.error('Failed to delete turf:', error)
            alert('Failed to delete turf. Please try again.')
        }
    }
}

function cancelEdit() {
    if (hasChanges.value) {
        const message = props.selectedTurf
            ? 'Are you sure you want to discard your changes?'
            : 'Are you sure you want to cancel?'

        if (!confirm(message)) {
            return
        }
    }

    // Reset selected tracts
    selectedTracts.value = []
    turfName.value = ''
    turfDetails.value = ''

    emit('close')
}
</script>

<template>
    <div id="map" class="map w-full h-full">
        <!-- Address search and Demographics stacked on top left -->
        <div class="absolute top-2.5 left-2.5 z-10 flex flex-col gap-2 max-w-md">
            <!-- Address Search -->
            <div v-if="map" class="bg-base-100 rounded-lg shadow-lg">
                <AddressSearch :map="map" :mapbox-token="MAPBOX_TOKEN" @result-selected="handleAddressSearchResult" />
            </div>

            <!-- Demographics overlay -->
            <div v-if="mode === 'edit'" class="demographics-card bg-base-100 rounded-lg shadow-lg overflow-hidden">
                <DemographicsOverlay :selectedTurf="selectedTurf as TurfWithColors" />
            </div>
        </div>

        <!-- Name & Description Modal (for new turfs) -->
        <div v-if="showNameDescriptionModal" class="modal-overlay">
            <div class="modal-content">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-3xl font-bold">Create New Turf</h2>
                    <button type="button" class="btn btn-sm btn-circle btn-ghost" @click="closeNameDescriptionModal"
                        aria-label="Close">
                        ✕
                    </button>
                </div>

                <div class="divider mt-0"></div>

                <form @submit.prevent="proceedToDrawing" class="space-y-6">
                    <div class="form-control">
                        <label class="label" for="turf-name-modal">
                            <span class="label-text font-semibold">Turf Name</span>
                        </label>
                        <input id="turf-name-modal" v-model="turfName" type="text" placeholder="Enter turf name"
                            maxlength="100" class="input input-bordered w-full focus:input-primary" required />
                    </div>

                    <div class="form-control">
                        <label class="label" for="turf-details-modal">
                            <span class="label-text font-semibold">Description</span>
                        </label>
                        <textarea id="turf-details-modal" v-model="turfDetails" placeholder="Enter turf description"
                            rows="5" maxlength="500"
                            class="textarea textarea-bordered w-full focus:textarea-primary resize-none"
                            required></textarea>
                    </div>

                    <div class="form-control">
                        <label class="label">
                            <span class="label-text font-semibold">Go to a location on the map (Optional)</span>
                        </label>
                           <div class="relative h-8">
                         <AddressSearch v-if="map" :map="map" :mapbox-token="MAPBOX_TOKEN"
                            @result-selected="handleAddressSearchResult" />
                       </div>
                    </div>

                    <div class="flex gap-3">
                        <button type="submit" class="btn btn-primary gap-2">
                            Next: Draw on Map
                        </button>
                        <button type="button" class="btn gap-2" @click="closeNameDescriptionModal">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Edit Form Modal (opened from edit button) -->
        <div v-if="showEditFormModal" class="modal-overlay">
            <div class="modal-content">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-3xl font-bold">
                        {{ selectedTurf ? 'Edit Turf Details' : 'Edit Turf' }}
                    </h2>
                    <button type="button" class="btn btn-sm btn-circle btn-ghost" @click="closeEditForm"
                        aria-label="Close">
                        ✕
                    </button>
                </div>

                <div class="divider mt-0"></div>

                <form @submit.prevent="saveTurf" class="space-y-6">
                    <div class="form-control">
                        <label class="label" for="turf-name-edit">
                            <span class="label-text font-semibold">Turf Name</span>
                        </label>
                        <input id="turf-name-edit" v-model="turfName" type="text" placeholder="Enter turf name"
                            maxlength="100" class="input input-bordered w-full focus:input-primary" required />
                    </div>

                    <div class="form-control">
                        <label class="label" for="turf-details-edit">
                            <span class="label-text font-semibold">Description</span>
                        </label>
                        <textarea id="turf-details-edit" v-model="turfDetails" placeholder="Enter turf description"
                            rows="5" maxlength="500"
                            class="textarea textarea-bordered w-full focus:textarea-primary resize-none"
                            required></textarea>
                    </div>

                    <div class="card bg-base-200 shadow-sm">
                        <div class="card-body p-2">
                            <div class="flex items-center gap-3">
                                <div class="badge badge-lg gap-2"
                                    :class="selectedTracts.length > 0 ? 'badge-info' : 'badge-warning'">
                                    {{ selectedTracts.length }} tract{{ selectedTracts.length !== 1 ? 's' : '' }}
                                </div>
                                <div class="flex-1">
                                    <p class="text-sm" v-if="selectedTracts.length === 0">
                                        Click on the map to select census tracts
                                    </p>
                                    <p class="text-sm" v-else>
                                        Selected and ready to save
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="flex gap-3">
                        <button type="submit" class="btn btn-primary gap-2" :disabled="!isFormValid">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
                                stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M5 13l4 4L19 7" />
                            </svg>
                            Save Changes
                        </button>
                        <button type="button" class="btn gap-2" @click="closeEditForm">
                            Close
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Edit mode controls -->
        <div v-if="mode === 'edit' && !showNameDescriptionModal"
            class="edit-controls absolute top-2.5 right-2.5 z-10 bg-base-100 rounded-lg shadow-lg px-3 py-4">

            <div class="form-control mb-3">
                <div class="btn-group w-full">
                    <button class="btn btn-sm flex-1" :class="editMode === 'draw' ? 'btn-info' : 'btn-ghost'"
                        @click="editMode = 'draw'">
                        <span class="mr-1">✏️</span>
                        <span>Draw</span>
                    </button>
                    <button class="btn btn-sm flex-1" :class="editMode === 'erase' ? 'btn-error' : 'btn-ghost'"
                        @click="editMode = 'erase'">
                        <span class="mr-1">🧽</span>
                        <span>Erase</span>
                    </button>
                </div>
            </div>

            <div class="form-control mb-3">
                <label class="label py-0 mb-1">
                    <span class="label-text">Selection Size: {{ selectionRadius }}</span>
                </label>
                <input id="selection-radius" type="range" v-model.number="selectionRadius" min="1" max="10" step="1"
                    class="range range-info range-sm" />
            </div>

            <div class="form-control mb-3">
                <button @click="undo" :disabled="selectionHistory.length === 0" class="btn btn-info btn-sm w-full">
                    <span class="mr-1">↩️</span>
                    <span>Undo ({{ selectionHistory.length }})</span>
                </button>
            </div>


            <div class="py-2 px-1">
                <p class="text-sm"><strong>{{ selectedTurf ? 'Editing:' : 'Creating:' }}</strong> {{ selectedTurf?.name || turfName  }}</p>
            </div>
               <div class="mb-3">
                <button @click="openEditForm" class="btn btn-sm w-full">
                    Change Name & Description
                </button>
            </div>


            <div class="divider"></div>

         
            <div class="flex flex-col gap-2">
                <button v-if="hasChanges" @click="saveTurf" :disabled="!isFormValid"
                    class="btn btn-primary btn-sm w-full gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    {{ selectedTurf ? 'Update Turf' : 'Save Turf' }}
                </button>

                <button @click="cancelEdit" class="btn btn-sm w-full gap-2">
                    {{ hasChanges ? 'Cancel' : 'Close' }}
                </button>

                <button v-if="selectedTurf" @click="deleteTurf" class="btn btn-error btn-sm w-full gap-2">
                    Delete Turf
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
#map {
    width: 100%;
    height: 100%;
}

.demographics-card {
    margin-top: 2.5rem;
    max-height: 60vh;
    overflow-y: auto;
    width: 100%;
}

.modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
}

.modal-content {
    background-color: white;
    border-radius: 0.5rem;
    padding: 2rem;
    max-width: 600px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.input:focus,
.textarea:focus {
    outline: none;
    border-color: hsl(var(--p));
}

@media (max-width: 768px) {
    .demographics-card {
        max-height: 40vh;
    }
}
</style>