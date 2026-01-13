<script lang="ts" setup>
import { computed, onMounted, ref, toRaw, watch, type Ref } from 'vue';
import { useMapStore } from '@/stores/map';
import { useTurfStore, type DemographicsResponse } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import { demographicMetrics } from '@/stores/metrics';
import { demographicsApi } from '@/services/api';
import { debounce } from '@/utils';
import * as d3 from "d3";

const mapStore = useMapStore()
const turfStore = useTurfStore()
const { selectedTracts } = storeToRefs(mapStore)
const { selectedTurf, demographics, loadingDemographics, demographicsError } = storeToRefs(turfStore)

const getCategories = computed(() => {
    return [...new Set(demographicMetrics.map((metric) => metric.category))];
});

const getMetricsByCategory = (category: string) => {
    return demographicMetrics.filter((metric) => metric.category === category);
};


const isEditing = ref(false)
const turfName = ref('')
const turfDetails = ref('')
const selectedTractsDemographics: Ref<DemographicsResponse | null> = ref(null)

const isFormValid = computed(() => {
    return turfName.value.trim() !== '' &&
        turfDetails.value.trim() !== '' &&
        selectedTracts.value.length > 0
})

// Compute the difference between current turf and selected tracts
const getDifference = (metricId: string) => {
    const turfValue = demographics.value?.aggregated?.[metricId]
    const tractsValue = selectedTractsDemographics.value?.aggregated?.[metricId]

    if (turfValue === undefined || tractsValue === undefined) return null

    // todo check if number to avoid issues
    try {
        const diff = Number(tractsValue) - Number(turfValue)
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
    const format = d3.format('0,.2f') // todo- use metrics store to figure decimals 
    if (diff === null) return 'N/A'
    if (diff === 0) return '0'
    return diff > 0 ? `+${format(diff)}` : `${format(diff)}`
}

watch(isEditing, (value) => {
    // toggle on editing mode for the map using the map store
    mapStore.setMode(value ? 'edit' : 'view')
})

watch(selectedTracts, debounce(async () => {
    const tracts = toRaw(selectedTracts.value)
    if (tracts.length) {
        const demographics = await demographicsApi.getByTracts(tracts)
        selectedTractsDemographics.value = demographics
    } else {
        selectedTractsDemographics.value = null
    }

}, 400))

onMounted(() => {
    const turf = selectedTurf.value
    //  populate the form
    turfName.value = turf?.name ?? ''
    turfDetails.value = turf?.details ?? ''
})


function saveTurf() {
    if (!isFormValid.value) return

    if (selectedTurf.value) {
        // Update existing turf
        turfStore.updateTurf(selectedTurf.value.id, {
            name: turfName.value.trim(),
            details: turfDetails.value.trim(),
            tracts: [...selectedTracts.value]
        })
    } else {
        // Create new turf
        turfStore.addTurf({
            name: turfName.value.trim(),
            details: turfDetails.value.trim(),
            tracts: [...selectedTracts.value]
        })
    }

    // Reset form and exit edit mode
    turfName.value = ''
    turfDetails.value = ''
    isEditing.value = false
}
const hasChanges = computed(() => {
    if (!selectedTurf.value) {
        return turfName.value.trim() !== '' ||
            turfDetails.value.trim() !== '' ||
            selectedTracts.value.length > 0
    } else {
        return turfName.value !== selectedTurf.value.name ||
            turfDetails.value !== selectedTurf.value.details ||
            JSON.stringify([...selectedTracts.value].sort()) !==
            JSON.stringify([...selectedTurf.value.tracts].sort())
    }
})

function cancelEdit() {
    if (hasChanges.value) {
        const message = selectedTurf.value
            ? 'Are you sure you want to discard your changes?'
            : 'Are you sure you want to cancel?'

        if (!confirm(message)) {
            return
        }
    }
    isEditing.value = false
    mapStore.setMode('view')
}

async function deleteTurf() {
    if (!selectedTurf.value) return

    const confirmMessage = `Are you sure you want to delete "${selectedTurf.value.name}"? This action cannot be undone.`

    if (confirm(confirmMessage)) {
        try {
            await turfStore.deleteTurf(selectedTurf.value.id)
            // Reset state after successful deletion
            turfName.value = ''
            turfDetails.value = ''
            isEditing.value = false
            mapStore.setMode('view')
        } catch (error) {
            alert('Failed to delete turf. Please try again.')
        }
    }
}


</script>

<template>

    <h2 class="title is-4">{{ selectedTurf ? 'Edit Turf' : 'Create New Turf' }}</h2>
    <form @submit.prevent="saveTurf">
        <div class="field">
            <label class="label" for="turf-name">Name</label>
            <div class="control">
                <input id="turf-name" v-model="turfName" class="input" type="text" placeholder="Enter turf name"
                    maxlength="100" />
            </div>
        </div>

        <div class="field">
            <label class="label" for="turf-details">Description</label>
            <div class="control">
                <textarea id="turf-details" v-model="turfDetails" class="textarea" placeholder="Enter turf description"
                    rows="4" maxlength="500"></textarea>
            </div>
        </div>

        <div class="field">
            <div class="notification" :class="selectedTracts.length > 0 ? 'is-info is-light' : 'is-warning is-light'">
                <p class="is-size-7">
                    <strong>{{ selectedTracts.length }}</strong> tract(s) selected
                </p>
                <p class="is-size-7 mt-1" v-if="selectedTracts.length === 0">
                    Please select at least one tract on the map
                </p>
            </div>
        </div>

        <div class="field is-grouped">
            <div class="control" v-if="hasChanges">
                <button type="submit" class="button is-primary" :disabled="!isFormValid">
                    <span>{{ selectedTurf ? 'Update Turf' : 'Save Turf' }}</span>
                </button>
            </div>
            <div class="control">
                <button type="button" class="button is-light" @click="cancelEdit">
                    {{ hasChanges ? 'Cancel' : 'Close' }}
                </button>
            </div>
            <div class="control" v-if="selectedTurf">
                <button type="button" class="button is-danger" @click="deleteTurf">
                    Delete Turf
                </button>
            </div>
        </div>
    </form>

    <div v-if="selectedTurf" class="demographic-metrics mt-3">
        <div v-if="loadingDemographics">Loading...</div>
        <div v-else-if="demographicsError" class="has-text-danger">{{ demographicsError }}</div>
        <div v-else-if="demographics?.aggregated">
            <div v-for="category in getCategories" :key="category" class="mb-4">
                <h6 class="subtitle is-6">{{ category }}</h6>
                <table class="table is-fullwidth is-bordered comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th class="has-text-centered">Current Turf</th>
                            <th class="has-text-centered">Selected Tracts</th>
                            <th class="has-text-centered">Difference</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="metric in getMetricsByCategory(category)" :key="metric.id">
                            <td class="metric-name">{{ metric.name }}</td>
                            <td class="metric-value has-text-centered">
                                {{ demographics.aggregated[metric.id] ?? 'N/A' }}
                            </td>
                            <td class="metric-value has-text-centered">
                                {{ selectedTractsDemographics?.aggregated?.[metric.id] ?? 'N/A' }}
                            </td>
                            <td class="has-text-centered">
                                <span class="tag" :class="getDifferenceClass(getDifference(metric.id))">
                                    {{ formatDifference(getDifference(metric.id)) }}
                                </span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        <div v-else>No demographic data available.</div>
    </div>

</template>

<style scoped>
.close-button {
    position: absolute;
    top: 0;
    right: 0;
    z-index: 10;
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