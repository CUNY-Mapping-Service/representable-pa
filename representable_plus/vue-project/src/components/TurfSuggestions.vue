<script lang="ts" setup>
import { ref, computed, type Ref, onMounted } from 'vue';
import { useDefaultStore } from '@/stores/default';
import { storeToRefs } from 'pinia';
import { demographicMetrics } from '@/stores/metrics';
import {
    demographicsApi,
    turfApi,
    type DemographicsResponse,
    type TractSuggestion,
} from '@/services/api';
import * as d3 from 'd3';
import type { TurfWithColors } from '@/views/Landing.vue';

const props = defineProps<{
    selectedTurf: TurfWithColors;
}>();

const emit = defineEmits<{
    back: [];
}>();

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

const defaultStore = useDefaultStore();
const { selectedTracts, choroplethMetric } = storeToRefs(defaultStore);

const suggestions = ref<TractSuggestion[]>([]);
const suggestionsLoading = ref(false);
const suggestionsError = ref<string | null>(null);

const loadingStates: Ref<Record<number, boolean>> = ref({});
const suggestionDemographics: Ref<Record<number, any>> = ref({});
const previewedSuggestionId: Ref<number | null> = ref(null);
const demographics: Ref<DemographicsResponse | null> = ref(null);

const getCategories = computed(() => {
    return [...new Set(demographicMetrics.map((metric) => metric.category))];
});

const getMetricsByCategory = (category: string) => {
    return demographicMetrics.filter((metric) => metric.category === category);
};

const getDifference = (metricId: string, suggestionDemo: DemographicsResponse | null) => {
    const turfValue = demographics.value?.aggregated?.[metricId];
    const suggestionValue = suggestionDemo?.aggregated?.[metricId];

    if (turfValue === undefined || suggestionValue === undefined) return null;

    try {
        const diff = Number(suggestionValue) - Number(turfValue);
        return diff;
    } catch {
        return null;
    }
};

const getDifferenceBadgeClass = (diff: number | null) => {
    if (diff === null) return 'badge-ghost';
    if (diff === 0) return 'badge-ghost';
    return diff > 0 ? 'badge-success' : 'badge-error';
};

const formatDifference = (diff: number | null) => {
    const format = d3.format('0,');
    if (diff === null) return 'N/A';
    if (diff === 0) return '0';
    return diff > 0 ? `+${format(diff)}` : `${format(diff)}`;
};

// (Optional now; can be removed if unused)
const formatValue = (value: unknown) => {
    if (value === undefined || value === null) return 'N/A';
    const format = d3.format('0,.2f');
    return format(Number(value));
};

async function loadTurfDemographics() {
    try {
        const data = await demographicsApi.getByTracts(props.selectedTurf.tracts);
        demographics.value = data;
    } catch (error) {
        console.error('Failed to load turf demographics:', error);
    }
}

async function loadSuggestionData(id: number, suggestedTracts: string[]) {
    if (suggestionDemographics.value[id]) return;
    const tracts = [...suggestedTracts, ...props.selectedTurf.tracts];

    loadingStates.value[id] = true;
    try {
        const demo = await demographicsApi.getByTracts(tracts);
        suggestionDemographics.value[id] = demo;
    } catch (error) {
        console.error('Failed to load suggestion demographics:', error);
        suggestionDemographics.value[id] = null;
    } finally {
        loadingStates.value[id] = false;
    }
}

function previewSuggestion(suggestion: TractSuggestion) {
    previewedSuggestionId.value = suggestion.id;
    // If you want preview of current + suggestion, use:
    // selectedTracts.value = [...props.selectedTurf.tracts, ...suggestion.tracts];
    selectedTracts.value = suggestion.tracts;
}

function applySuggestion(tracts: string[]) {
    const confirmMessage =
        'Apply this suggestion to your turf? This will replace your current tract selection.';
    if (confirm(confirmMessage)) {
        selectedTracts.value = tracts;
        defaultStore.setMode('edit');
    }
}

async function loadSuggestions() {
    if (!props.selectedTurf?.id) {
        suggestions.value = [];
        return;
    }

    suggestionsLoading.value = true;
    suggestionsError.value = null;
    try {
        const data = await turfApi.fetchSuggestions(props.selectedTurf);
        suggestions.value = data ?? [];
    } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        suggestionsError.value = 'Failed to load suggestions.';
        suggestions.value = [];
    } finally {
        suggestionsLoading.value = false;
    }
}

onMounted(() => {
    loadTurfDemographics();
    loadSuggestions();
});
</script>

<template>
    <div class="flex justify-between items-center mb-4">
        <h1 class="text-3xl font-bold">{{ selectedTurf.name }}</h1>
        <button type="button" class="btn" @click="emit('back')">
            Back
        </button>
    </div>

    <div class="container mb-5" v-if="demographics">
        <div class="current-demographics-grid">
            <div v-for="category in getCategories" :key="category" class="current-demographics-card">
                <h6 class="text-sm font-semibold mb-2">{{ category }}</h6>
                <table class="table table-xs w-full current-demographics-table">
                    <thead>
                        <tr>
                            <th class="metric-col">Metric</th>
                            <th class="value-col text-center">Current</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id"
                            :class="{ 'hover-row': true, 'clicked-row': choroplethMetric === metric.id }"
                            @click="defaultStore.setChoroplethMetric(metric.id)">
                            <td class="metric-name metric-col">{{ metric.name }}</td>
                            <td class="metric-value value-col text-center">
                                {{ formatNumber(demographics?.aggregated?.[metric.id]) }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="container">
        <h2 class="text-xl font-bold">Resources and Assets</h2>
        <p>
            Allow orgs to track their existing resources on the map, they can import a spreadsheet or
            from the resources below
        </p>
        <p>
            <a href="https://data.pa.gov/" target="_blank" rel="noopener noreferrer"
                class="link link-primary">data.pa</a>
        </p>
        <p>
            <a href="https://assets.wprdc.org/" target="_blank" rel="noopener noreferrer" class="link link-primary">
                https://assets.wprdc.org/
            </a>
        </p>
    </div>

    <div class="container">
        <h2 class="text-xl font-bold">Events</h2>
        <p>Track previous events and drives</p>
    </div>

    <div class="container suggestions-container">
        <h2 class="text-xl font-bold">Additional Tract Suggestions</h2>

        <div v-if="suggestionsLoading" class="alert alert-info">
            <span>Loading suggestions…</span>
        </div>

        <div v-else-if="suggestionsError" class="alert alert-error">
            <span>{{ suggestionsError }}</span>
        </div>

        <div v-else-if="!suggestions || suggestions.length === 0" class="alert alert-info">
            <span>No suggestions available for this turf.</span>
        </div>

        <div v-else class="suggestions-scroll-wrapper">
            <div class="suggestions-scroll">
                <div v-for="suggestion in suggestions" :key="suggestion.id"
                    class="suggestion-card card border-1 border-solid border-neutral-100"
                    :class="[previewedSuggestionId === suggestion.id ? 'preview' : '']"
                    @click="previewSuggestion(suggestion)"
                    @mouseenter="loadSuggestionData(suggestion.id, suggestion.tracts)">
                    <div class="card-header">
                        <div class="card-title">
                            <span class="badge badge-info mr-2">{{ suggestion.type }}</span>
                            {{ suggestion.tracts.length }} tract(s)
                        </div>
                    </div>

                    <div class="card-body">
                        <p class="mb-3">{{ suggestion.description }}</p>

                        <div v-if="loadingStates[suggestion.id]" class="text-center py-4">
                            <span class="text-xs">Loading demographics...</span>
                        </div>

                        <div v-else-if="suggestionDemographics[suggestion.id]">
                            <div v-for="category in getCategories" :key="category" class="mb-3">
                                <h6 class="text-sm font-semibold mb-2">{{ category }}</h6>
                                <table class="table table-xs w-full comparison-table">
                                    <thead>
                                        <tr>
                                            <th>Metric</th>
                                            <th class="text-center">Current</th>
                                            <th class="text-center">With Change</th>
                                            <th class="text-center">Diff</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id">
                                            <td class="metric-name">{{ metric.name }}</td>
                                            <td class="metric-value text-center">
                                                {{ formatNumber(demographics?.aggregated?.[metric.id]) }}
                                            </td>
                                            <td class="metric-value text-center">
                                                {{
                                                    formatNumber(
                                                        suggestionDemographics[suggestion.id]?.aggregated?.[metric.id],
                                                    )
                                                }}
                                            </td>
                                            <td class="text-center">
                                                <span class="badge badge-sm" :class="getDifferenceBadgeClass(
                                                    getDifference(
                                                        metric.id,
                                                        suggestionDemographics[suggestion.id],
                                                    ),
                                                )">
                                                    {{
                                                        formatDifference(
                                                            getDifference(
                                                                metric.id,
                                                                suggestionDemographics[suggestion.id],
                                                            ),
                                                        )
                                                    }}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div v-else class="text-center py-4 opacity-50">
                            <span class="text-xs">Hover or click to load demographics</span>
                        </div>
                    </div>

                    <div class="card-actions">
                        <button class="btn btn-ghost btn-sm w-full" @click.stop="applySuggestion(suggestion.tracts)">
                            Apply Suggestion
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.container {
    padding-bottom: 0.8rem;
    margin-bottom: 1rem;
    border-bottom: solid 1px hsl(var(--bc) / 0.2);
}

.suggestions-container {
    height: 100%;
}

.suggestions-scroll-wrapper {
    transform: rotateX(180deg);
    overflow-x: auto;
}

.suggestions-scroll {
    display: flex;
    gap: 1.5rem;
    padding-bottom: 1rem;
    scroll-snap-type: x mandatory;
    transform: rotateX(180deg);
}

.suggestion-card {
    min-width: 400px;
    max-width: 400px;
    flex-shrink: 0;
    scroll-snap-align: start;
    background-color: hsl(var(--b1));
    border-radius: 0.5rem;
    display: flex;
    flex-direction: column;
}

.suggestion-card.preview {
    background-color: hsl(var(--b2));
}

.suggestion-card:hover {
    background-color: hsl(var(--b2));
    cursor: pointer;
}

.card-header {
    padding: 1rem;
    border: 1px solid hsl(var(--bc) / 0.1);
}

.card-title {
    font-weight: 600;
    font-size: 1rem;
    display: flex;
    align-items: center;
}

.card-body {
    padding: 1rem;
    flex: 1;
}

.card-actions {
    padding: 0.5rem 1rem;
    border-top: 1px solid hsl(var(--bc) / 0.1);
}

.comparison-table {
    font-size: 0.75rem;
    background-color: transparent;
}

.comparison-table .metric-name {
    font-weight: 500;
    font-size: 0.75rem;
}

.comparison-table .metric-value {
    font-family: monospace;
    font-size: 0.75rem;
}

.comparison-table thead th {
    background-color: hsl(var(--b2));
    font-weight: 600;
    font-size: 0.7rem;
    padding: 0.5rem;
}

.comparison-table td {
    padding: 0.5rem;
}

.current-demographics-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
}

@media (max-width: 1200px) {
    .current-demographics-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}

@media (max-width: 900px) {
    .current-demographics-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 600px) {
    .current-demographics-grid {
        grid-template-columns: 1fr;
    }
}

.current-demographics-card {
    padding: 0.5rem 0.75rem;
    border: 1px solid hsl(var(--bc) / 0.2);
    border-radius: 0.25rem;
    background-color: hsl(var(--b2));
}

.current-demographics-table {
    table-layout: fixed;
    font-size: 0.7rem;
    margin-bottom: 0;
    background-color: transparent;
}

.current-demographics-table thead th {
    padding: 0.25rem 0.4rem;
    font-size: 0.65rem;
    background-color: hsl(var(--b3));
}

.current-demographics-table td {
    padding: 0.2rem 0.4rem;
}

.current-demographics-table .metric-col {
    width: 65%;
}

.current-demographics-table .value-col {
    width: 35%;
}

.current-demographics-table .metric-name {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.current-demographics-table .metric-value {
    font-family: monospace;
}

.hover-row:hover {
    cursor: pointer;
    background-color: hsl(var(--b3));
}

.clicked-row {
    background-color: hsl(var(--b3));
}
</style>
