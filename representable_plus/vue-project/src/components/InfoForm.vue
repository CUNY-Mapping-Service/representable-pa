<script lang="ts" setup>
import Map from '@/components/Map.vue'
import { useMapStore } from '@/stores/map';
import { useTurfStore } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import SearchTurfs from './SearchTurfs.vue';
import { formatDate } from '@/utils';

const {setMode} = useMapStore()
const turfStore = useTurfStore()
const { selectedTurf } = storeToRefs(turfStore)

</script>

<template>
    <!-- if no turf is selected give the user the option to add a new one -->
    <div v-if="!selectedTurf">
        <h3 class="title is-3">Turf dashboard</h3>
        <p class="subtitle is-5 is-spaced">Search existing public and your organization turfs; or create a new turf.</p>
        <button class="button mt-3" @click="setMode('edit')">Add a new turf</button>
        <h5 class="subtitle is-5 my-2">OR</h5>
    </div>
    <SearchTurfs />
    <!-- if a turf is selected. show a close button and information about the turf, allow the user to edit -->
    <div v-if="selectedTurf" class="turf-details mt-3" style="position: relative;">
        <div style="display:flex;  position: absolute; top: 0; right: 0;">
            <button class="button is-primary is-small" @click="setMode('edit')">
                <span>Edit Turf</span>
            </button>
            <button class="button is-white py-1" aria-label="close" @click="turfStore.clearSelectedTurf">
                <span class="icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                        aria-hidden="true">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </span>
            </button>
        </div>
        <p class="is-size-4 mb-2">{{ selectedTurf.name }}</p>
        <p class="is-size-5 has-text-grey-dark">{{ selectedTurf.details }}</p>
        <p class="is-size-7 has-text-grey mt-2">
            <strong>{{ selectedTurf.tracts?.length || 0 }}</strong> tract(s)
        </p>
        <p class="is-size-7 has-text-grey" v-if="selectedTurf.createdAt">
            Created: {{ formatDate(selectedTurf.createdAt) }}
        </p>
    </div>

</template>


<style scoped>
.turf-details {
    padding: 0.3rem;
}

.demographic-metrics {
    padding: 0 0.5rem;
}

.metric-card {
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2px solid transparent;
    height: 100%;
}

.metric-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

.metric-card.is-selected {
    border-color: #3e8ed0;
    background-color: #f0f7ff;
}

.metric-card .card-content {
    padding: 0.75rem;
}

.metric-card .media {
    align-items: flex-start;
}

.metric-card .media-left {
    margin-right: 0.75rem;
    padding-top: 0.25rem;
}

.radio-wrapper input[type="radio"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.metric-icon {
    font-size: 1rem;
    margin-bottom: 0.25rem;
}

.metric-name {
    font-weight: 600;
    font-size: 0.9rem;
    line-height: 1.3;
    margin-bottom: 0.25rem;
    color: #363636;
}

.metric-description {
    font-size: 0.75rem;
    color: #7a7a7a;
    line-height: 1.3;
}

.tag {
    font-size: 0.65rem;
}
</style>