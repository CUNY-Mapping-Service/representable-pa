<script setup lang="ts">
import { Map as MaplibreMap } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { computed, onMounted, ref, toRaw, watch } from 'vue';
import STYLE from '@/stores/default_style';
import { storeToRefs } from 'pinia';
import { useDefaultStore } from '@/stores/default';
import type { TurfWithColors } from '@/views/Landing.vue';

// d3 for bins
import { extent } from 'd3-array';
import { scaleQuantize } from 'd3-scale';

const props = defineProps<{
    turfs: TurfWithColors[],
    selectedTurf: TurfWithColors | null
}>();

const mapCenter = ref<[number, number]>([-75.2038894, 39.962347]);
const mapZoom = ref<number>(10.5);

const defaultStore = useDefaultStore();
const { map, selectedTracts, mode, choroplethMetric } = storeToRefs(defaultStore);

const isMapReady = ref(false);

// legend items derived from updateChoroplethLayer bins
const legendItems = ref<{ label: string; color: string }[]>([]);
const showLegend = computed(() => legendItems.value.length > 0);

onMounted(() => {
    const mapInstance = new MaplibreMap({
        container: 'map',
        // @ts-expect-error style incompat
        style: STYLE,
        center: mapCenter.value,
        zoom: mapZoom.value,
        attributionControl: false
    });

    mapInstance.on('load', () => {
        isMapReady.value = true;
        defaultStore.setMap(mapInstance);
        applyModeSettings(mode.value);
        updateTractColors();
        updateChoroplethLayer(); // in case choroplethMetric already set
    });
});

// Update colors whenever data or mode changes
watch(
    [() => props.turfs, () => props.selectedTurf, mode, selectedTracts],
    () => {
        updateTractColors();
    },
    { deep: true }
);

// Zoom to selected turf
watch(
    () => props.selectedTurf,
    (newTurf) => {
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
    }
);

// React to mode change
watch(mode, (newMode) => {
    applyModeSettings(newMode);
    updateTractColors();
});

// Enable/disable choropleth layer when choroplethMetric changes
watch(
    choroplethMetric,
    () => {
        updateChoroplethLayer();
    }
);

function clearAllFeatureStates() {
    if (!map.value || !isMapReady.value) return;
    map.value.removeFeatureState({ source: 'tracts', sourceLayer: 'tracts_2023' });
}

function applyModeSettings(newMode: string) {
    if (!map.value || !isMapReady.value) return;

    if (newMode === 'suggestion') {
        map.value.setLayoutProperty('turf-layer', 'visibility', 'visible');
        map.value.setLayoutProperty('tract-layer', 'visibility', 'visible');
        map.value.setLayoutProperty('tract-hover-layer', 'visibility', 'none');
    } else {
        // default: only show turf-layer
        map.value.setLayoutProperty('turf-layer', 'visibility', 'visible');
        map.value.setLayoutProperty('tract-layer', 'visibility', 'none');
        map.value.setLayoutProperty('tract-hover-layer', 'visibility', 'none');
    }
}

function updateTractColors() {
    if (!map.value || !isMapReady.value) return;

    const featureCollection = {
        type: 'FeatureCollection',
        features: toRaw(props.turfs).map((d) => ({
            type: 'Feature',
            properties: {
                name: d.name,
                id: d.id,
                color: d.fillColor,
                outlineColor: d.outlineColor
            },
            geometry: d.geometry
        }))
    };

    // @ts-expect-error setData not in typings
    map.value.getSource('turfs')?.setData(featureCollection);

    clearAllFeatureStates();

    if (mode.value === 'suggestion' && props.selectedTurf) {
        // Only show the selected turf
        map.value.setFilter('turf-layer', ['==', ['get', 'id'], props.selectedTurf.id]);

        // Highlight selected tracts
        selectedTracts.value.forEach((tractId) => {
            map.value!.setFeatureState(
                { source: 'tracts', sourceLayer: 'tracts_2023', id: tractId },
                { selected: true }
            );
        });
    } else if (mode.value === 'suggestion' && !props.selectedTurf) {
        // Show all turfs in suggestion mode if none is selected
        map.value.setFilter('turf-layer', null);
    } else {
        // Non-suggestion modes: show all turfs, no tract highlighting
        map.value.setFilter('turf-layer', null);
    }
}

/**
 * Enable the choropleth layer when choroplethMetric is not null,
 * and build a binned color expression + legend using d3.
 */
function updateChoroplethLayer() {
    if (!map.value || !isMapReady.value) return;

    const metric = 'ALAND'; // const metric = choroplethMetric.value;
    if (!metric) {
        map.value.setLayoutProperty('tract-choropleth', 'visibility', 'none');
        legendItems.value = [];
        return;
    }

    map.value.setLayoutProperty('tract-choropleth', 'visibility', 'visible');

    const features = map.value.queryRenderedFeatures({
        layers: ['tract-layer']
    });

    if (!features.length) {
        map.value.setPaintProperty('tract-choropleth', 'fill-color', '#ccc');
        legendItems.value = [];
        return;
    }

    // collect metric values for visible features
    const values: number[] = [];
    for (const f of features) {
        const v = Number(f.properties?.[metric]);
        if (!Number.isNaN(v)) values.push(v);
    }

    if (!values.length) {
        map.value.setPaintProperty('tract-choropleth', 'fill-color', '#ccc');
        legendItems.value = [];
        return;
    }

    const domain = extent(values); // [number | undefined, number | undefined]

    const min = domain[0];
    const max = domain[1];

    if (min == null || max == null) {
        map.value.setPaintProperty('tract-choropleth', 'fill-color', '#ccc');
        legendItems.value = [];
        return;
    }

    // define color ramp and d3 quantize scale -> bins
    const colors = ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'];
    const scale = scaleQuantize<string>()
        .domain([min, max])
        .range(colors);

    const thresholds = scale.thresholds(); // number[]

    // Maplibre expression using step() with thresholds from d3
    const fillExpression: any[] = ['step', ['to-number', ['get', metric]], colors[0]];
    thresholds.forEach((t, i) => {
        fillExpression.push(t, colors[i + 1]);
    });

    map.value.setPaintProperty('tract-choropleth', 'fill-color', fillExpression);

    // Build legend items from bins
    const items: { label: string; color: string }[] = [];

    if (thresholds.length > 0) {
        items.push({
            label: `${formatNumber(min)} – ${formatNumber(thresholds[0] ?? 0)}`,
            color: colors[0] || 'gray'
        });
        for (let i = 1; i < thresholds.length; i++) {
            items.push({
                label: `${formatNumber(thresholds[i - 1] ?? 0)} – ${formatNumber(thresholds[i] ?? 0)}`,
                color: colors[i] || 'gray'
            });
        }
        items.push({
            label: `${formatNumber(thresholds[thresholds.length - 1] ?? 0)} – ${formatNumber(max)}`,
            color: colors[colors.length - 1] || 'gray'
        });
    } else {
        items.push({
            label: `${formatNumber(min)}`,
            color: colors[0] || 'gray'
        });
    }

    legendItems.value = items;
}

function formatNumber(v: number): string {
    if (Math.abs(v) >= 1_000_000) {
        return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    }
    if (Math.abs(v) >= 1_000) {
        return (v / 1_000).toFixed(1).replace(/\.0$/, '') + 'k';
    }
    return v.toFixed(0);
}
</script>

<template>
    <div class="map-wrapper">
        <div v-if="showLegend" class="legend">
            <div v-for="item in legendItems" :key="item.label" class="legend-item">
                <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
                <div>{{ item.label }}</div>
            </div>
        </div>

        <div id="map" class="map"></div>
    </div>
</template>

<style scoped>
.map-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
}

#map {
    width: 100%;
    height: 100%;
    flex: 1 1 auto;
}

/* Legend styles */

.legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    background: #fff;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid #ddd;
}

.legend-color {
    width: 10px;
    height: 10px;
    border-radius: 3px;
    border: 1px solid #ddd;
}
</style>
