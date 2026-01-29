<script lang="ts" setup>
import InteractiveMap from '@/components/InteractiveMap.vue';
import TurfGeometryPreview from '@/components/TurfGeometryPreview.vue';
import DemographicsOverlay from '@/components/DemographicsOverlay.vue';
import TurfSuggestions from '@/components/TurfSuggestions.vue';
import { turfApi, type Turf } from '@/services/api';
import { useDefaultStore } from '@/stores/default';
import { getTurfColor, getTurfOutlineColor } from '@/utils/colors';
import { storeToRefs } from 'pinia';
import { computed, nextTick, onMounted, ref } from 'vue';
import EditTurfOverlay from '@/components/EditTurfOverlay.vue';

const defaultStore = useDefaultStore()
const { mode } = storeToRefs(defaultStore)

export interface TurfWithColors extends Turf {
    fillColor: string;
    outlineColor: string;
}

const turfs = ref<TurfWithColors[]>([])
const selectedTurf = ref<TurfWithColors | null>(null)
const editOverlayCollapsed = ref(false)
const demographicsOverlayCollapsed = ref(false)

const searchQuery = ref('')

// for searching
const filteredTurfs = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    if (!q) return turfs.value

    return turfs.value.filter(turf => {
        const name = (turf.name || '').toLowerCase()
        const details = (turf.details || '').toLowerCase()
        return name.includes(q) || details.includes(q)
    })
})

const modeMapSize = computed(() => {
    switch (mode.value) {
        case 'view':
            return 'map-1-4-size'
        case 'edit':
            return 'map-full-size'
        case 'suggestion':
            return 'map-1-4-size'
        default:
            return ''
    }
})

async function loadTurfs() {
    const updatedTurfs = await turfApi.loadTurfs()
    turfs.value = updatedTurfs.map((d: any, i) => {
        const fillColor = getTurfColor(i)
        const outlineColor = getTurfOutlineColor(fillColor)
        d.fillColor = fillColor
        d.outlineColor = outlineColor
        return d as TurfWithColors
    })
}

onMounted(() => {
    loadTurfs()
})

const toggleNewTurf = async function () {
    selectedTurf.value = null
    await nextTick();
    if (mode.value !== 'edit') {
        defaultStore.setMode('edit')
    } else {
        defaultStore.setMode('view')
    }
}

const editTurf = function (turf: TurfWithColors) {
    defaultStore.setMode('edit')
    selectedTurf.value = turf
}

const viewSuggestions = function (turf: TurfWithColors) {
    selectedTurf.value = turf
    defaultStore.setMode('suggestion')
}

const handleEditClose = () => {
    selectedTurf.value = null
    defaultStore.setMode('view')
}

const handleEditSave = async () => {
    // Reload turfs after save
    await loadTurfs()
}

const handleSuggestionsBack = () => {
    selectedTurf.value = null
    defaultStore.setMode('view')
}
</script>

<template>
    <main>
        <div class="map-container" :class="[modeMapSize]">
            <InteractiveMap :turfs="turfs as TurfWithColors[]" :selectedTurf="selectedTurf as TurfWithColors" />
        </div>
        <div class="overlay">
            <div class="buttons" v-show="!!selectedTurf && mode === 'view'">
                <button class="button is-small" type="button" @click="selectedTurf = null">
                    Clear selected turf
                </button>
                <button class="button is-small is-info" type="button" @click="selectedTurf = null">
                    Edit
                </button>
            </div>

        </div>

        <div v-if="mode === 'view'" class="info-container">
            <h2 class="title is-3 has-text-grey-dark m-0">Turf Data Manager</h2>
            <h3>
                Drawing a turf allows you to track and organize information for census outreach!
                Start by creating a new turf or selecting an existing one below. You may also view
                key demographics of the area.
            </h3>

            <div>
                <div class="card mb-5 is-clickable" @click="toggleNewTurf()">
                    <div class="card-content has-text-centered pt-2 pb-3">
                        <p class="title">+</p>
                        <p class="subtitle is-size-6 is-italic">Draw a new turf</p>
                    </div>
                </div>

                <div class="field mb-5">
                    <div class="control">
                        <input class="input" type="text" placeholder="Search turfs by name or description..."
                            v-model="searchQuery">
                    </div>

                    <div class="mt-3">
                        <button class="button is-small" type="button" @click="selectedTurf = null"
                            v-show="!!selectedTurf">
                            Clear selected turf
                        </button>
                    </div>
                    <div class="masonry mt-4">
                        <div v-for="turf in filteredTurfs" :key="turf.id" class="masonry-item">
                            <div class="card" @click="selectedTurf = turf" style="cursor: pointer;">
                                <div class="card-content">
                                    <div class="media">
                                        <div class="media-content">
                                            <p class="title is-5">
                                                {{ turf.name || 'Untitled Turf' }}
                                            </p>
                                            <p class="subtitle is-7">
                                                ID: {{ turf.id }}, # Tracts:
                                                <strong>{{ turf.tracts.length }}</strong>
                                            </p>
                                        </div>
                                        <div class="media-right">
                                            <button class="button is-small is-info" title="Edit turf"
                                                @click.stop="editTurf(turf as TurfWithColors)">
                                                Edit
                                            </button>
                                        </div>
                                    </div>

                                    <div class="content">
                                        <p>
                                            {{ turf.details || 'No details provided.' }}
                                        </p>

                                        <p class="is-size-7 m-0">
                                            Population : <strong></strong>
                                        </p>
                                        <p class="is-size-7 m-0">
                                            Households : <strong></strong>
                                        </p>

                                        <div class="mt-3">
                                            <TurfGeometryPreview :geometry="turf.geometry" :fillColor="turf.fillColor"
                                                :outlineColor="turf.outlineColor" />
                                        </div>

                                        <div class="mt-3">
                                            <button class="button is-small is-info is-fullwidth"
                                                @click.stop="viewSuggestions(turf as TurfWithColors)">
                                                View Details
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-if="filteredTurfs.length === 0" class="masonry-item has-text-centered has-text-grey">
                            No turfs match your search.
                        </div>
                    </div>


                </div>
            </div>

        </div>

        <div v-else-if="mode === 'edit'" class="overlay">
            <button class="button is-light back-button" type="button" aria-label="Back to view mode"
                @click="handleEditClose()">
                🢨
            </button>

            <div class="demographics-overlay" :class="{ 'collapsed': demographicsOverlayCollapsed }">
                <DemographicsOverlay v-if="!demographicsOverlayCollapsed"
                    :selectedTurf="selectedTurf as TurfWithColors" />
            </div>

            <button class="collapse-tab collapse-tab-left" type="button"
                @click="demographicsOverlayCollapsed = !demographicsOverlayCollapsed"
                :title="demographicsOverlayCollapsed ? 'Expand Demographics' : 'Collapse Demographics'">
                <svg v-if="demographicsOverlayCollapsed" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M6 3l5 5-5 5z" fill="currentColor" />
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M10 3L5 8l5 5z" fill="currentColor" />
                </svg>
            </button>

            <div class="edit-overlay" :class="{ 'collapsed': editOverlayCollapsed }">
                <EditTurfOverlay v-if="!editOverlayCollapsed" :selectedTurf="selectedTurf as TurfWithColors"
                    @close="handleEditClose" @save="handleEditSave" />
            </div>

            <button class="collapse-tab collapse-tab-right" type="button"
                @click="editOverlayCollapsed = !editOverlayCollapsed"
                :title="editOverlayCollapsed ? 'Expand Editor' : 'Collapse Editor'">
                <svg v-if="editOverlayCollapsed" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M10 3L5 8l5 5z" fill="currentColor" />
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M6 3l5 5-5 5z" fill="currentColor" />
                </svg>
            </button>
        </div>

        <div v-else-if="mode === 'suggestion'" class="info-container">
            <TurfSuggestions :selectedTurf="selectedTurf as TurfWithColors" @back="handleSuggestionsBack" />
        </div>
    </main>
</template>

<style scoped>
main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    position: relative;
}

.map-container {
    width: 100%;
    position: relative;
}

.map-1-4-size {
    flex: 0 0 30vh;
}

.map-full-size {
    flex: 1 1 auto;
}

.info-container {
    padding: 1rem 1.2rem;
    overflow-y: auto;
    overflow-x: hidden;
    flex: 1 1 auto;
}

.info-container .card:hover {
    background-color: rgb(233, 233, 233);
}

..overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.back-button,
.edit-overlay,
.demographics-overlay,
.collapse-tab {
    pointer-events: auto;
}

.demographics-overlay {
    position: absolute;
    bottom: 0;
    left: 1rem;
    z-index: 2;
    background-color: #fff;
    padding: .5rem;
    border-radius: 5px;
    margin: 5px;
    box-shadow: 2px 2px 8px #a9a9a9;
    max-width: min(45vw, 55rem);
    height: 50vh;
    overflow-y: auto;
    transition: transform 0.3s ease, opacity 0.3s ease;
}

.demographics-overlay.collapsed {
    transform: translateX(calc(-100% - 0.5rem));
    opacity: 0;
    pointer-events: none;
}

.edit-overlay {
    position: absolute;
    bottom: 0;
    right: 1rem;
    z-index: 2;
    background-color: #fff;
    padding: .5rem;
    border-radius: 5px;
    margin: 5px;
    box-shadow: 2px 2px 8px #a9a9a9;
    width: 55vw;
    height: 50vh;
    overflow-y: auto;
    transition: transform 0.3s ease, opacity 0.3s ease;
}

.edit-overlay.collapsed {
    transform: translateX(calc(100% + 0.5rem));
    opacity: 0;
    pointer-events: none;
}

.collapse-tab {
    position: absolute;
    top: calc(50% - 1.5rem);
    width: 1.75rem;
    height: 3rem;
    background-color: #f5f5f5;
    border: 1px solid #dbdbdb;
    border-radius: 0.5rem;
    box-shadow: 2px 2px 8px #a9a9a9;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 3;
    color: #363636;
    padding: 0;
}

.collapse-tab:hover {
    background-color: #e8e8e8;
}

.collapse-tab-left {
    left: calc(1rem + 0.25rem);
}

.collapse-tab-right {
    right: calc(1rem + 0.25rem);
}

.collapse-tab svg {
    display: block;
}

.back-button {
    position: absolute;
    top: 0.6rem;
    left: 0.6rem;
    z-index: 3;
    border-radius: 6px;
    box-shadow: 2px 2px 8px #a9a9a9;
}

.buttons {
    pointer-events: none;
    display: flex;
    position: absolute;
    top: 0.6rem;
    left: 0.6rem;
    z-index: 3;
}

.buttons button {
    pointer-events: all;
    box-shadow: 2px 2px 8px #a9a9a9;
}

.masonry {
    column-count: 3;
    column-gap: 1rem;
}

.masonry-item {
    break-inside: avoid;
    margin-bottom: 1rem;
}

/* Match Bulma-ish breakpoints */
@media (max-width: 1023px) {
    .masonry {
        column-count: 2;
    }
}

@media (max-width: 768px) {
    .masonry {
        column-count: 1;
    }
}
</style>