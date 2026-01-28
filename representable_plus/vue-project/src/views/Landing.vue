<script lang="ts" setup>
import InteractiveMap from '@/components/InteractiveMap.vue';
import TurfGeometryPreview from '@/components/TurfGeometryPreview.vue';
import { turfApi, type Turf } from '@/services/api';
import { useDefaultStore } from '@/stores/default';
import { getTurfColor, getTurfOutlineColor } from '@/utils/colors';
import { storeToRefs } from 'pinia';
import { computed, nextTick, onMounted, ref } from 'vue';

const defaultStore = useDefaultStore()
const { mode } = storeToRefs(defaultStore)

export interface TurfWithColors extends Turf {
    fillColor: string;
    outlineColor: string;
}

const turfs = ref<TurfWithColors[]>([])
const selectedTurf = ref<TurfWithColors | null>(null)

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
        case 'suggestion':
            return 'map-full-size'
        default:
            return ''
    }
})

onMounted(() => {
    turfApi.loadTurfs().then(updatedTurfs => {
        turfs.value = updatedTurfs.map((d: any, i) => {
            const fillColor = getTurfColor(i)
            const outlineColor = getTurfOutlineColor(fillColor)
            d.fillColor = fillColor
            d.outlineColor = outlineColor
            return d as TurfWithColors
        })
    })
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
</script>

<template>
    <main>
        <div class="map-container" :class="[modeMapSize]">
            <InteractiveMap :turfs="turfs" :selectedTurf="selectedTurf" />
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
                        <button class="button is-small is-dark" type="button" @click="selectedTurf = null"
                            v-show="!!selectedTurf">
                            Clear selected tract
                        </button>
                    </div>

                    <div class="columns is-multiline mt-4">
                        <div v-for="turf in filteredTurfs" :key="turf.id"
                            class="column is-one-third-desktop is-half-tablet is-full-mobile">
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
                                            <button class="button is-small is-light" title="Edit turf"
                                                @click="editTurf(turf)">
                                                ✏️
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
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-if="filteredTurfs.length === 0" class="column is-full has-text-centered has-text-grey">
                            No turfs match your search.
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <div v-else-if="mode === 'edit'" class="overlay">
            <button class="button is-light back-button" type="button" aria-label="Back to view mode"
                @click="toggleNewTurf()">
                🢨
            </button>
            <div class="edit-overlay">h4</div>
        </div>
        <div v-else-if="mode === 'suggestion'" class="is-relative">

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


.overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.back-button,
.edit-overlay {
    pointer-events: auto;
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
    min-width: max(50vw, 30rem);
    min-height: 3rem;
}

.back-button {
    position: absolute;
    top: 0.6rem;
    left: 0.6rem;
    z-index: 3;
    border-radius: 6px;
    box-shadow: 2px 2px 8px #a9a9a9;
}
</style>