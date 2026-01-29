<script lang="ts" setup>
import { ref, computed, type Ref } from 'vue';
import { useMapStore } from '@/stores/map';
import { useTurfStore, type DemographicsResponse, type TractSuggestion } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import { demographicMetrics } from '@/stores/metrics';
import { demographicsApi } from '@/services/api';
import * as d3 from "d3";

const mapStore = useMapStore()
const { setMode } = mapStore
const turfStore = useTurfStore()
const { suggestions, selectedTurf, demographics } = storeToRefs(turfStore)

const loadingStates: Ref<Record<number, boolean>> = ref({})
const suggestionDemographics: Ref<Record<number, any>> = ref({})
const previewedSuggestionId: Ref<number> = ref(0)

const getCategories = computed(() => {
    return [...new Set(demographicMetrics.map((metric) => metric.category))];
});

const getMetricsByCategory = (category: string) => {
    return demographicMetrics.filter((metric) => metric.category === category);
};

const getDifference = (metricId: string, suggestionDemo: DemographicsResponse | null) => {
    const turfValue = demographics.value?.aggregated?.[metricId]
    const suggestionValue = suggestionDemo?.aggregated?.[metricId]

    if (turfValue === undefined || suggestionValue === undefined) return null

    try {
        const diff = Number(suggestionValue) - Number(turfValue)
        return diff
    } catch (error) {
        return null
    }
}

const getDifferenceClass = (diff: number | null) => {
    if (diff === null) return 'is-light'
    if (diff === 0) return 'is-light'
    return diff > 0 ? 'is-success' : 'is-danger'
}

const formatDifference = (diff: number | null) => {
    const format = d3.format('0,.2f')
    if (diff === null) return 'N/A'
    if (diff === 0) return '0'
    return diff > 0 ? `+${format(diff)}` : `${format(diff)}`
}

const formatValue = (value: any) => {
    if (value === undefined || value === null) return 'N/A'
    const format = d3.format('0,.2f')
    return format(Number(value))
}

async function loadSuggestionData(index: number, suggestedTracts: string[]) {
    if (suggestionDemographics.value[index]) return // Already loaded
    const tracts = [...suggestedTracts, ...selectedTurf.value?.tracts ?? []]

    loadingStates.value[index] = true
    try {
        const demo = await demographicsApi.getByTracts(tracts)
        suggestionDemographics.value[index] = demo
    } catch (error) {
        console.error('Failed to load suggestion demographics:', error)
        suggestionDemographics.value[index] = null
    } finally {
        loadingStates.value[index] = false
    }
}

function previewSuggestion(suggestion: TractSuggestion){
    previewedSuggestionId.value = suggestion.id
    mapStore.setSelectedTracts(suggestion.tracts)
}


function applySuggestion(tracts: string[]) {
    if (!selectedTurf.value) return

    const confirmMessage = `Apply this suggestion to your turf? This will replace your current tract selection.`
    if (confirm(confirmMessage)) {
        mapStore.setSelectedTracts(tracts)
        setMode('edit')
    }
}
</script>

<template>
    <div class="suggestions-container">
        <div class="level mb-4">
            <div class="level-left">
                <div class="level-item">
                    <h2 class="title is-4">Tract Suggestions</h2>
                </div>
            </div>
            <div class="level-right">
                <div class="level-item">
                    <button type="button" class="button is-light" @click="setMode('view')">
                        Back
                    </button>
                </div>
            </div>
        </div>
        <div v-if="!suggestions || suggestions.length === 0" class="notification is-info is-light">
            <p>No suggestions available for this turf.</p>
        </div>

 
        <div v-else class="suggestions-scroll-wrapper">
            <div class="suggestions-scroll">
                <div v-for="suggestion in suggestions" :key="suggestion.id" class="suggestion-card card"
                    :class="[previewedSuggestionId === suggestion.id ? 'preview' : '']" 
                    @click="previewSuggestion(suggestion)"
                    v-intersect="{ callback: () => loadSuggestionData(suggestion.id, suggestion.tracts), once: true, options: { threshold: 0.25 } }">

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
                                                        formatValue(suggestionDemographics[suggestion.id]?.aggregated?.[metric.id])
                                                    }}
                                                </td>
                                                <td class="has-text-centered">
                                                    <span class="tag is-small"
                                                        :class="getDifferenceClass(getDifference(metric.id, suggestionDemographics[suggestion.id]))">
                                                        {{ formatDifference(getDifference(metric.id,
                                                            suggestionDemographics[suggestion.id])) }}
                                                    </span>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    <footer class="card-footer">
                        <a class="card-footer-item" @click="applySuggestion(suggestion.tracts)">
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
    padding: 1rem;
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