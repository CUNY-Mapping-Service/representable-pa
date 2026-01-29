<script lang="ts" setup>
import { computed, onMounted, ref, type Ref } from 'vue';
import { useDefaultStore } from '@/stores/default';
import { storeToRefs } from 'pinia';
import { getBaseRoute } from '@/services/api';
import type { TurfWithColors } from '@/views/Landing.vue';

const props = defineProps<{
    selectedTurf: TurfWithColors | null
}>()

const emit = defineEmits<{
    close: []
    save: []
}>()

const defaultStore = useDefaultStore()
const { selectedTracts, mode } = storeToRefs(defaultStore)

const turfName = ref('')
const turfDetails = ref('')

const isFormValid = computed(() => {
    return turfName.value.trim() !== '' &&
        turfDetails.value.trim() !== '' &&
        selectedTracts.value.length > 0
})

onMounted(() => {
    // Populate the form with existing turf data
    turfName.value = props.selectedTurf?.name ?? ''
    turfDetails.value = props.selectedTurf?.details ?? ''
})

async function saveTurf() {
    if (!isFormValid.value) return

    try {
        const payload = {
            name: turfName.value.trim(),
            details: turfDetails.value.trim(),
            tracts: [...selectedTracts.value]
        }

        let response;
        if (props.selectedTurf) {
            // Update existing turf
            response = await fetch(`${getBaseRoute()}/edit/${props.selectedTurf.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
        } else {
            // Create new turf
            response = await fetch(`${getBaseRoute()}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
        }

        if (!response.ok) {
            throw new Error('Failed to save turf')
        }

        // Emit save event to trigger refresh in parent
        emit('save')

        // Reset form
        turfName.value = ''
        turfDetails.value = ''
        selectedTracts.value = []

        // Close the editor
        emit('close')
    } catch (error) {
        console.error('Failed to save turf:', error)
        alert('Failed to save turf. Please try again.')
    }
}

const hasChanges = computed(() => {
    if (!props.selectedTurf) {
        return turfName.value.trim() !== '' ||
            turfDetails.value.trim() !== '' ||
            selectedTracts.value.length > 0
    } else {
        return turfName.value !== props.selectedTurf.name ||
            turfDetails.value !== props.selectedTurf.details ||
            JSON.stringify([...selectedTracts.value].sort()) !==
            JSON.stringify([...props.selectedTurf.tracts].sort())
    }
})

function cancelEdit() {
    if (hasChanges.value) {
        const message = props.selectedTurf
            ? 'Are you sure you want to discard your changes?'
            : 'Are you sure you want to cancel?'

        if (!confirm(message)) {
            return
        }
    }

    // Reset selected tracts
    selectedTracts.value = []

    emit('close')
}

async function deleteTurf() {
    if (!props.selectedTurf) return

    const confirmMessage = `Are you sure you want to delete "${props.selectedTurf.name}"? This action cannot be undone.`

    if (confirm(confirmMessage)) {
        try {
            const response = await fetch(`${getBaseRoute()}/edit/${props.selectedTurf.id}`, {
                method: 'DELETE'
            })

            if (!response.ok) {
                throw new Error('Failed to delete turf')
            }

            // Reset state after deletion
            turfName.value = ''
            turfDetails.value = ''
            selectedTracts.value = []

            // Emit save to trigger refresh and close
            emit('save')
            emit('close')
        } catch (error) {
            console.error('Failed to delete turf:', error)
            alert('Failed to delete turf. Please try again.')
        }
    }
}
</script>

<template>
    <div class="turf-edit-container">
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
                        Click on the map to select census tracts
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
    </div>
</template>

<style scoped>
.turf-edit-container {
    height: 100%;
    overflow-y: auto;
    padding: 1rem;
}
</style>