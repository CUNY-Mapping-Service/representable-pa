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

const defaultStore = useDefaultStore();
const { selectedTracts } = storeToRefs(defaultStore);

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

const getDifferenceClass = (diff: number | null) => {
    if (diff === null) return 'is-light';
    if (diff === 0) return 'is-light';
    return diff > 0 ? 'is-success' : 'is-danger';
};

const formatDifference = (diff: number | null) => {
    const format = d3.format('0,.2f');
    if (diff === null) return 'N/A';
    if (diff === 0) return '0';
    return diff > 0 ? `+${format(diff)}` : `${format(diff)}`;
};

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
    <div class="level mb-4">
        <div class="level-left">
            <div class="level-item">
                <h1 class="title is-2">{{ selectedTurf.name }}</h1>
            </div>
        </div>
        <div class="level-right">
            <div class="level-item">
                <button type="button" class="button is-light" @click="emit('back')">
                    Back to Turfs
                </button>
            </div>
        </div>
    </div>
    <div>
        <h2 class="title is-4">Assets </h2>

        <p>Open Data Preview??<a href="https://data.pa.gov/" target="_blank" rel="noopener noreferrer">data.pa</a></p>
    </div>

    <div>
        <h2 class="title is-4">Events</h2>

    </div>

    <div class="suggestions-container">

        <h2 class="title is-4">Tract Suggestions</h2>


        <div v-if="suggestionsLoading" class="notification is-info is-light">
            <p>Loading suggestions…</p>
        </div>

        <div v-else-if="suggestionsError" class="notification is-danger is-light">
            <p>{{ suggestionsError }}</p>
        </div>

        <div v-else-if="!suggestions || suggestions.length === 0" class="notification is-info is-light">
            <p>No suggestions available for this turf.</p>
        </div>

        <div v-else class="suggestions-scroll-wrapper">
            <div class="suggestions-scroll">
                <div v-for="suggestion in suggestions" :key="suggestion.id" class="suggestion-card card"
                    :class="[previewedSuggestionId === suggestion.id ? 'preview' : '']"
                    @click="previewSuggestion(suggestion)"
                    @mouseenter="loadSuggestionData(suggestion.id, suggestion.tracts)">
                    <header class="card-header">
                        <p class="card-header-title">
                            <span class="tag is-info mr-2">{{ suggestion.type }}</span>
                            {{ suggestion.tracts.length }} tract(s)
                        </p>
                    </header>

                    <div class="card-content">
                        <div class="content">
                            <p class="mb-3">{{ suggestion.description }}</p>

                            <div v-if="loadingStates[suggestion.id]" class="has-text-centered py-4">
                                <span class="is-size-7">Loading demographics...</span>
                            </div>

                            <div v-else-if="suggestionDemographics[suggestion.id]">
                                <div v-for="category in getCategories" :key="category" class="mb-3">
                                    <h6 class="subtitle is-6 mb-2">{{ category }}</h6>
                                    <table class="table is-narrow is-fullwidth comparison-table">
                                        <thead>
                                            <tr>
                                                <th>Metric</th>
                                                <th class="has-text-centered">Current</th>
                                                <th class="has-text-centered">With Change</th>
                                                <th class="has-text-centered">Diff</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id">
                                                <td class="metric-name">{{ metric.name }}</td>
                                                <td class="metric-value has-text-centered">
                                                    {{ formatValue(demographics?.aggregated?.[metric.id]) }}
                                                </td>
                                                <td class="metric-value has-text-centered">
                                                    {{
                                                        formatValue(
                                                            suggestionDemographics[suggestion.id]?.aggregated?.[metric.id],
                                                        )
                                                    }}
                                                </td>
                                                <td class="has-text-centered">
                                                    <span class="tag is-small" :class="getDifferenceClass(
                                                        getDifference(metric.id, suggestionDemographics[suggestion.id]),
                                                    )
                                                        ">
                                                        {{
                                                            formatDifference(
                                                                getDifference(metric.id, suggestionDemographics[suggestion.id]),
                                                            )
                                                        }}
                                                    </span>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div v-else class="has-text-centered py-4 has-text-grey-light">
                                <span class="is-size-7">Hover to load demographics</span>
                            </div>
                        </div>
                    </div>

                    <footer class="card-footer">
                        <a class="card-footer-item" @click.stop="applySuggestion(suggestion.tracts)">
                            <span class="icon-text">
                                <span>Apply Suggestion</span>
                            </span>
                        </a>
                    </footer>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
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
}

.suggestion-card.preview {
    background-color: rgba(214, 214, 214, 0.5);
}

.suggestion-card:hover {
    background-color: rgba(214, 214, 214, 0.4);
    cursor: pointer;
}

.comparison-table {
    font-size: 0.75rem;
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
    background-color: #f5f5f5;
    font-weight: 600;
    font-size: 0.7rem;
    padding: 0.5rem;
}

.comparison-table td {
    padding: 0.5rem;
}

.card-footer-item {
    cursor: pointer;
}

.card-footer-item:hover {
    background-color: #f5f5f5;
}
</style>
