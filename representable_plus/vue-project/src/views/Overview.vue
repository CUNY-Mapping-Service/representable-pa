<script lang="ts" setup>
import Map from '@/components/Map.vue'
import { computed, onMounted, ref, watch } from 'vue';
import { useMapStore } from '@/stores/map';
import { useTurfStore } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import InfoForm from '@/components/InfoForm.vue';

const mapStore = useMapStore()
const turfStore = useTurfStore()
const { map, selectedTracts, mode } = storeToRefs(mapStore)
const { selectedTurf, turfs } = storeToRefs(turfStore)


onMounted(() => {
    turfStore.loadTurfs();
})

const isEditing = ref(false)
const turfName = ref('')
const turfDetails = ref('')

const isFormValid = computed(() => {
    return turfName.value.trim() !== '' &&
        turfDetails.value.trim() !== '' &&
        selectedTracts.value.length > 0
})

watch(isEditing, (value) => {
    // toggle on editing mode for the map using the map store
    mapStore.setMode(value ? 'edit' : 'view')
})

watch(selectedTurf, (turf) => {
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
    <main>
        <div class="map-container">
            <Map></Map>
        </div>
        <div class="container">
            <div v-if="mode === 'view'">
                <InfoForm></InfoForm>
            </div>
            <div v-else-if="mode === 'edit'">
                <h2 class="title is-4">{{ selectedTurf ? 'Edit Turf' : 'Create New Turf' }}</h2>
                <form @submit.prevent="saveTurf">
                    <div class="field">
                        <label class="label" for="turf-name">Name</label>
                        <div class="control">
                            <input id="turf-name" v-model="turfName" class="input" type="text"
                                placeholder="Enter turf name" maxlength="100" />
                        </div>
                    </div>

                    <div class="field">
                        <label class="label" for="turf-details">Description</label>
                        <div class="control">
                            <textarea id="turf-details" v-model="turfDetails" class="textarea"
                                placeholder="Enter turf description" rows="4" maxlength="500"></textarea>
                        </div>
                    </div>

                    <div class="field">
                        <div class="notification"
                            :class="selectedTracts.length > 0 ? 'is-info is-light' : 'is-warning is-light'">
                            <p class="is-size-7">
                                <strong>{{ selectedTracts.length }}</strong> tract(s) selected
                            </p>
                            <p class="is-size-7 mt-1" v-if="selectedTracts.length === 0">
                                Please select at least one tract on the map
                            </p>
                        </div>
                    </div>

                    <div class="field is-grouped">
                        <div class="control">
                            <button type="submit" class="button is-primary" :disabled="!isFormValid">
                                <span>{{ selectedTurf ? 'Update Turf' : 'Save Turf' }}</span>
                            </button>
                        </div>
                        <div class="control">
                            <button type="button" class="button is-light" @click="cancelEdit">
                                Cancel
                            </button>
                        </div>
                        <div class="control" v-if="selectedTurf">
                            <button type="button" class="button is-danger" @click="deleteTurf">
                                Delete Turf
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </main>

</template>

<style scoped>
main {
    display: flex;
    max-height: 100vh;
}

.container {
    flex: 1;
    padding: 1rem 1.2rem;
    max-height: 100vh;
    overflow-y: scroll;
    overflow-x: hidden;
}

.map-container {
    position: relative;
    flex: 1;
    order: -1;
    height: 100vh;
}

.close-button {
    position: absolute;
    top: 0;
    right: 0;
    z-index: 10;
}
</style>