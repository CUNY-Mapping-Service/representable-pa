<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import MapboxGeocoder from '@mapbox/mapbox-gl-geocoder';
import '@mapbox/mapbox-gl-geocoder/dist/mapbox-gl-geocoder.css';
import type { Map as MaplibreMap } from 'maplibre-gl';
import { LngLatBounds } from 'maplibre-gl';
import { v4 as uuidv4 } from 'uuid';

interface Props {
    map: MaplibreMap | null;
    mapboxToken: string;
}

interface AdditionalQuery {
    pattern: RegExp;
    name: string;
    type: 'census' | 'other';
    process: (match: RegExpMatchArray, matchedString: string) => Promise<{
        url: string;
        data: any;
        matchedPattern: string;
        matchedString: string;
        type: 'census' | 'other';
        extent?: [[number, number], [number, number]];
        latlng?: [number, number];
    } | null>;
}

const props = defineProps<Props>();
const emit = defineEmits<{
    (e: 'result-selected', data: { feature: any; additionalData: any[] }): void;
}>();

const geocoderContainer = ref<HTMLDivElement>();
const sessionToken = ref(uuidv4());
const searchQuery = ref('');
const isLocating = ref(false);
let geocoderInstance: MapboxGeocoder | null = null;

const showGeolocateButton = computed(() => !searchQuery.value.trim());

const additionalQueries: AdditionalQuery[] = [
    {
        // Match any Census GEOID (e.g., 1400000US36055009401, 2500000US2205)
        pattern: /^\s*(\d+)US(\d+)\s*$/,
        name: 'Census Geography (All)',
        type: 'census',
        process: async (_match: RegExpMatchArray, featureId: string) => {
            try {
                const cleanFeatureId = featureId.trim();
                const url = `https://data.census.gov/api/profile/metadata?g=${cleanFeatureId}&includeHighlights=false`;
                const response = await fetch(url);
                const data = await response.json();

                const extent = data?.header?.map?.extent;

                return {
                    url,
                    data,
                    matchedPattern: /^\s*(\d+)US(\d+)\s*$/.toString(),
                    matchedString: cleanFeatureId,
                    type: 'census' as const,
                    extent: extent || undefined
                };
            } catch (error) {
                console.error('Error fetching Census Data:', error);
                return null;
            }
        }
    },
    {
        // Match 11-digit census tract IDs (e.g., 36055009401)
        pattern: /^\s*\d{11}\s*$/,
        name: 'Census Tract',
        type: 'census',
        process: async (match: RegExpMatchArray, matchedString: string) => {
            try {
                const tractId = match[0].trim();
                // Build full Census GEOID for tract level: 1400000US<TRACTID>
                const featureId = `1400000US${tractId}`;
                const url = `https://data.census.gov/api/profile/metadata?g=${featureId}&includeHighlights=false`;
                const response = await fetch(url);
                const data = await response.json();

                const extent = data?.header?.map?.extent;

                return {
                    url,
                    data,
                    matchedPattern: /^\s*\d{11}\s*$/.toString(),
                    matchedString,
                    type: 'census' as const,
                    extent: extent || undefined
                };
            } catch (error) {
                console.error('Error fetching Census Tract Data:', error);
                return null;
            }
        }
    }
];

async function fetchAdditionalDataFromStrings(searchStrings: string[]): Promise<any[]> {
    const results: any[] = [];

    for (const query of additionalQueries) {
        for (const searchString of searchStrings) {
            const match = String(searchString).match(query.pattern);
            if (match) {
                const result = await query.process(match, searchString);
                if (result) {
                    results.push(result);
                }
            }
        }
    }

    return results;
}


function zoomToExtent(extent: [[number, number], [number, number]]) {
    if (!props.map) return;

    const bounds = new LngLatBounds(
        [extent[0][0], extent[0][1]],
        [extent[1][0], extent[1][1]]
    );

    props.map.fitBounds(bounds, {
        padding: {
            top: 50,
            right: 50,
            bottom: 150,
            left: 50
        },
        duration: 1500
    });
}

function zoomToLatLng(latlng: [number, number], zoom: number = 14) {
    if (!props.map) return;

    props.map.flyTo({
        center: [latlng[1], latlng[0]],
        zoom,
        duration: 1500
    });
}

function handleGeolocate() {
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }

    isLocating.value = true;

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            zoomToLatLng([latitude, longitude], 15);

            emit('result-selected', {
                feature: {
                    center: [longitude, latitude],
                    place_name: 'Your Location',
                    place_type: ['geolocation'],
                    properties: {
                        is_user_location: true
                    }
                },
                additionalData: []
            });

            isLocating.value = false;
        },
        (error) => {
            console.error('Geolocation error:', error);
            let message = 'Unable to retrieve your location';

            switch (error.code) {
                case error.PERMISSION_DENIED:
                    message = 'Location permission denied';
                    break;
                case error.POSITION_UNAVAILABLE:
                    message = 'Location information unavailable';
                    break;
                case error.TIMEOUT:
                    message = 'Location request timed out';
                    break;
            }

            alert(message);
            isLocating.value = false;
        },
        {
            enableHighAccuracy: false,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Custom render function
function customRender(item: any) {
    const title = item.place_name || item.text || 'Unknown';
    const address = item.place_type ? item.place_type.join(', ') : '';

    return `
    <div class="mapboxgl-ctrl-geocoder--suggestion">
      <div class="mapboxgl-ctrl-geocoder--suggestion-title">${title}</div>
      <div class="mapboxgl-ctrl-geocoder--suggestion-address">${address}</div>
    </div>
  `;
}

async function additionalQueryFeaturesFromQuery(query: string): Promise<any[]> {
    const extraData = await fetchAdditionalDataFromStrings([query]);
    const features: any[] = [];
    for (const data of extraData) {
        if (data.type === 'census' && data.data?.info) {
            const extent = data.data.header?.map?.extent;

            features.push({
                id: `census-${data.matchedString}`,
                type: 'Feature',
                place_type: ['Census Geography'],
                place_name: data.data.info.name,
                text: data.data.info.name,
                properties: {
                    census_data: data.data,
                    is_census_result: true,
                    extent
                }
            });
        }
    }

    return features;
}

onMounted(() => {
    if (!geocoderContainer.value || !props.map) return;

    geocoderInstance = new MapboxGeocoder({
        accessToken: props.mapboxToken,
        mapboxgl: props.map as any,
        marker: false,
        placeholder: 'Search for an address or a place',
        flyTo: false,
        render: customRender,
        externalGeocoder: async (query: string) => {
            try {
                const extraFeatures = await additionalQueryFeaturesFromQuery(query);
                return extraFeatures;
            } catch (e) {
                console.error('externalGeocoder error', e);
                return [];
            }
        }
    });

    geocoderContainer.value.appendChild(
        geocoderInstance.onAdd(props.map as any)
    );

    // Track search input changes
    const inputElement = geocoderContainer.value.querySelector('input');
    if (inputElement) {
        inputElement.addEventListener('input', (e) => {
            searchQuery.value = (e.target as HTMLInputElement).value;
        });

        inputElement.addEventListener('clear', () => {
            searchQuery.value = '';
        });
    }

    geocoderInstance.on('result', async (e: { result: any; }) => {
        const feature = e.result;

        if (feature.properties?.is_census_result) {
            const censusData = feature.properties.census_data;
            if (censusData?.header?.map?.extent) {
                zoomToExtent(censusData.header.map.extent);
            }

            emit('result-selected', {
                feature,
                additionalData: [
                    {
                        name: 'Census Data',
                        data: censusData,
                        type: 'census'
                    }
                ]
            });
        } else {
            const [lng, lat] = feature.center;
            if (lat || lng) zoomToLatLng([lat as number, lng as number]);

            emit('result-selected', {
                feature,
                additionalData: []
            });
        }
    });

    geocoderInstance.on('clear', () => {
        searchQuery.value = '';
    });

    geocoderInstance.on('results', () => {
        sessionToken.value = uuidv4();
    });
});
</script>

<template>
    <div class="address-search-container">
        <div ref="geocoderContainer" class="geocoder-wrapper"></div>
        <button v-if="showGeolocateButton" class="geolocate-button" :class="{ 'is-locating': isLocating }"
            @click="handleGeolocate" :disabled="isLocating" title="Use my location">
            <span class="text-xl" v-if="!isLocating">⚲</span>
            <svg v-else class="spinner" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
        </button>
    </div>
</template>

<style scoped>
.address-search-container {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 1;
    display: flex;
    gap: 8px;
    align-items: flex-start;
    width: 100%;
}

.geocoder-wrapper {
    flex: 1;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder) {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    width: 100%;
    max-width: 100%;
    font-size: 14px;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder input) {
    height: 40px;
    padding: 6px 35px;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder--suggestion) {
    padding: 8px 12px;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder--suggestion-title) {
    font-weight: 500;
    color: #333;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder--suggestion-address) {
    font-size: 12px;
    color: #666;
    margin-top: 2px;
}

.geocoder-wrapper :deep(.mapboxgl-ctrl-geocoder--suggestion:has([data-census-result])) {
    background-color: #f0f9ff;
    border-left: 3px solid #0284c7;
}

.geolocate-button {
    height: 40px;
    width: 40px;
    min-width: 40px;
    background: white;
    border: none;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
    transition: all 0.2s ease;
}

.geolocate-button:hover:not(:disabled) {
    background: #f5f5f5;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.geolocate-button:active:not(:disabled) {
    transform: scale(0.95);
}

.geolocate-button:disabled {
    cursor: not-allowed;
    opacity: 0.6;
}

.geolocate-button.is-locating {
    color: #0284c7;
}

.spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}

</style>
