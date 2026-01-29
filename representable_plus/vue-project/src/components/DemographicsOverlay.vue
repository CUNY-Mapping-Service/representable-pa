<script lang="ts" setup>
import { computed, onMounted, ref, toRaw, watch, type Ref } from 'vue';
import { useDefaultStore } from '@/stores/default';
import { storeToRefs } from 'pinia';
import { demographicMetrics } from '@/stores/metrics';
import { demographicsApi, type DemographicsResponse } from '@/services/api';
import { debounce } from '@/utils';
import * as d3 from 'd3';
import type { TurfWithColors } from '@/views/Landing.vue';

const props = defineProps<{
    selectedTurf: TurfWithColors;
}>();

const defaultStore = useDefaultStore();
const { selectedTracts } = storeToRefs(defaultStore);

const demographics: Ref<DemographicsResponse | null> = ref(null); // base
const selectedTractsDemographics: Ref<DemographicsResponse | null> = ref(null); // comparison
const loadingDemographics = ref(false);
const demographicsError = ref<string | null>(null);

/**
 * Derived data and formating 
 */
const getCategories = computed(() => [
    ...new Set(demographicMetrics.map((metric) => metric.category)),
]);

const getMetricsByCategory = (category: string) =>
    demographicMetrics.filter((metric) => metric.category === category);

const formatNumber = (raw: unknown) => {
    if (raw === null || raw === undefined) return 'N/A';

    const num = Number(raw);
    if (Number.isNaN(num)) return String(raw);

    // if the value is between 0 and 1, assumes percentages by default
    if (num > 0 && num < 1) {
        return `${d3.format('0,.2f')(num * 100)}%`;
    }

    return d3.format('0,.2f')(num);
};

/**
 * Tracts source
 */

const isUsingSelectedTractsAsBase = computed(() => {
    const turfTracts = props.selectedTurf?.tracts;
    return !turfTracts || turfTracts.length === 0;
});

// Base tracts (what the "Current Turf" column represents)
const baseTracts = computed<string[]>(() => {
    const turfTracts = props.selectedTurf?.tracts;
    if (turfTracts && turfTracts.length) return turfTracts;
    return toRaw(selectedTracts.value);
});

// Comparison tracts (only used when base is a real turf; otherwise we don't compare)
const comparisonTracts = computed<string[] | null>(() => {
    if (isUsingSelectedTractsAsBase.value) return null;
    const tracts = toRaw(selectedTracts.value);
    return tracts.length ? tracts : null;
});

/**
 * Fetch helpers
 */
const fetchDemographics = async (tracts: string[]): Promise<DemographicsResponse | null> => {
    if (!tracts || !tracts.length) return null;
    return demographicsApi.getByTracts(tracts);
};

const loadBaseDemographics = async () => {
    loadingDemographics.value = true;
    demographicsError.value = null;

    try {
        const tracts = baseTracts.value;
        demographics.value = await fetchDemographics(tracts);
    } catch (error) {
        console.error('Failed to load base demographics:', error);
        demographicsError.value = `Failed to load demographic data, ${error}`;
        demographics.value = null;
    } finally {
        loadingDemographics.value = false;
    }
};

const loadComparisonDemographics = async () => {
    // Only load comparison when base is a turf-based selection
    if (isUsingSelectedTractsAsBase.value) {
        selectedTractsDemographics.value = null;
        return;
    }

    try {
        const tracts = comparisonTracts.value;
        if (!tracts) {
            selectedTractsDemographics.value = null;
            return;
        }
        selectedTractsDemographics.value = await fetchDemographics(tracts);
    } catch (error) {
        console.error('Failed to load demographics for selected tracts:', error);
        selectedTractsDemographics.value = null;
    }
};

/**
 * Difference helpers
 */
const getDifference = (metricId: string) => {
    // Disable difference when base comes from selectedTracts
    if (isUsingSelectedTractsAsBase.value) return null;

    const turfValue = demographics.value?.aggregated?.[metricId];
    const tractsValue = selectedTractsDemographics.value?.aggregated?.[metricId];

    if (turfValue === undefined || tractsValue === undefined) return null;

    const diff = Number(tractsValue) - Number(turfValue);
    return Number.isNaN(diff) ? null : diff;
};

const getDifferenceClass = (diff: number | null) => {
    if (diff === null || diff === 0) return 'is-light';
    return diff > 0 ? 'is-success' : 'is-danger';
};

const formatDifference = (diff: number | null) => {
    const format = d3.format('0,.2f');
    if (diff === null) return 'N/A';
    if (diff === 0) return '0';
    return diff > 0 ? `+${format(diff)}` : `${format(diff)}`;
};

/**
 * Watchers
 */

// changes in base tracts (turf or selectedTracts fallback)
watch(
    baseTracts,
    debounce(() => {
        loadBaseDemographics();
    }, 400),
    { immediate: true }
);

// changes to comparison tracts  (only when a real turf is present)
watch(
    () => comparisonTracts.value,
    debounce(() => {
        loadComparisonDemographics();
    }, 400),
    { immediate: true }
);

onMounted(() => {
    loadBaseDemographics();
    loadComparisonDemographics();
});
</script>

<template>
    <div class="demographics-container">
        <h2 class="title is-4">Demographics Comparison</h2>

        <div v-if="loadingDemographics" class="has-text-centered">
            <p>Loading demographic data...</p>
        </div>

        <div v-else-if="demographicsError" class="notification is-danger is-light">
            {{ demographicsError }}
        </div>

        <div v-else-if="demographics?.aggregated">
            <div v-for="category in getCategories" :key="category" class="mb-5">
                <h6 class="subtitle is-6 has-text-weight-semibold">
                    {{ category }}
                </h6>

                <table class="table is-fullwidth is-bordered is-striped comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th class="has-text-centered">
                                {{ isUsingSelectedTractsAsBase ? 'Selected Tracts' : 'Current Turf' }}
                            </th>
                            <th v-if="!isUsingSelectedTractsAsBase" class="has-text-centered">
                                Selected Tracts
                            </th>
                            <th v-if="!isUsingSelectedTractsAsBase" class="has-text-centered">
                                Difference
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id">
                            <td class="metric-name">
                                {{ metric.name }}
                            </td>

                            <!-- Base value (turf or selectedTracts fallback) -->
                      <td class="metric-value has-text-centered">
  {{ formatNumber(demographics.aggregated[metric.id]) }}
</td>

                            <!-- Comparison only shown when a real turf exists -->
                          <td
  v-if="!isUsingSelectedTractsAsBase"
  class="metric-value has-text-centered"
>
  {{ formatNumber(selectedTractsDemographics?.aggregated?.[metric.id]) }}
</td>
                            <td v-if="!isUsingSelectedTractsAsBase" class="has-text-centered">
                                <span class="tag" :class="getDifferenceClass(getDifference(metric.id))">
                                    {{ formatDifference(getDifference(metric.id)) }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div v-else class="notification is-light">
            No demographic data available.
        </div>
    </div>
</template>

<style scoped>
.demographics-container {
    height: 100%;
    overflow-y: auto;
    padding: 1rem;
}

.comparison-table {
    font-size: 0.875rem;
}

.comparison-table .metric-name {
    font-weight: 500;
}

.comparison-table .metric-value {
    font-family: monospace;
}

.comparison-table thead th {
    background-color: #f5f5f5;
    font-weight: 600;
}
</style>
