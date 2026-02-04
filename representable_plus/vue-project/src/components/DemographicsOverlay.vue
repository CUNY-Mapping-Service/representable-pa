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

    // if the value contains a decimal, assumes percentages by default
    if (String(num).includes('.')) {
        return `${d3.format('0,.2f')(num)}%`;
    }

    return d3.format('0,')(num);
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
    if (diff === null || diff === 0) return 'badge-ghost';
    return diff > 0 ? 'badge-success' : 'badge-error';
};

const formatDifference = (diff: number | null) => {
    const format = d3.format('0,');
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
    <div class="h-full overflow-y-auto p-3 bg-base-100 rounded-md">
        <h2 class="text-2xl font-bold mb-6">Demographics Comparison</h2>

        <div v-if="loadingDemographics" class="text-center py-8">
            <span class="loading loading-spinner loading-lg"></span>
            <p class="mt-4">Loading demographic data...</p>
        </div>

        <div v-else-if="demographicsError" class="alert alert-error">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none"
                viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ demographicsError }}</span>
        </div>

        <div v-else-if="demographics?.aggregated" class="space-y-8">
            <div v-for="category in getCategories" :key="category">
                <h6 class="text-lg font-semibold mb-3">
                    {{ category }}
                </h6>

                <div class="overflow-x-auto">
                    <table class="table table-zebra w-full">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th class="text-center">
                                    {{ isUsingSelectedTractsAsBase ? 'Selected Tracts' : 'Current Turf' }}
                                </th>
                                <th v-if="!isUsingSelectedTractsAsBase" class="text-center">
                                    Selected Tracts
                                </th>
                                <th v-if="!isUsingSelectedTractsAsBase" class="text-center">
                                    Difference
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id">
                                <td class="font-medium">
                                    {{ metric.name }}
                                </td>

                                <!-- Base value (turf or selectedTracts fallback) -->
                                <td class="text-center font-mono">
                                    {{ formatNumber(demographics.aggregated[metric.id]) }}
                                </td>

                                <!-- Comparison only shown when a real turf exists -->
                                <td v-if="!isUsingSelectedTractsAsBase" class="text-center font-mono">
                                    {{ formatNumber(selectedTractsDemographics?.aggregated?.[metric.id]) }}
                                </td>
                                <td v-if="!isUsingSelectedTractsAsBase" class="text-center">
                                    <span class="badge" :class="getDifferenceClass(getDifference(metric.id))">
                                        {{ formatDifference(getDifference(metric.id)) }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div v-else class="alert">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                class="stroke-info shrink-0 w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>No demographic data available.</span>
        </div>
    </div>
</template>

<style scoped>
.table {
    font-size: 0.875rem;
}
</style>
