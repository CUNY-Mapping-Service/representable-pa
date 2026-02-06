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
    <div class="h-full overflow-y-scroll p-3 bg-base-100 rounded-md">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-3xl font-bold">
                {{ selectedTurf ? 'Edit Turf' : 'Create New Turf' }}
            </h2>
            <button type="button" class="btn btn-sm btn-circle btn-ghost" @click="cancelEdit" aria-label="Close">
                ✕
            </button>
        </div>

        <div class="divider mt-0"></div>

        <form @submit.prevent="saveTurf" class="space-y-6">
            <div class="form-control">
                <label class="label" for="turf-name">
                    <span class="label-text font-semibold">Turf Name</span>
                </label>
                <input id="turf-name" v-model="turfName" type="text" placeholder="Enter turf name" maxlength="100"
                    class="input input-bordered w-full focus:input-primary" required />
            </div>

            <div class="form-control">
                <label class="label" for="turf-details">
                    <span class="label-text font-semibold">Description</span>
                </label>
                <textarea id="turf-details" v-model="turfDetails" placeholder="Enter turf description" rows="5"
                    maxlength="500" class="textarea textarea-bordered w-full focus:textarea-primary resize-none"
                    required></textarea>
            </div>

            <div class="card bg-base-200 shadow-sm">
                <div class="card-body p-2">
                    <div class="flex items-center gap-3">
                        <div class="badge badge-lg gap-2"
                            :class="selectedTracts.length > 0 ? 'badge-info' : 'badge-warning'">
                            {{ selectedTracts.length }} tract{{ selectedTracts.length !== 1 ? 's' : '' }}
                        </div>
                        <div class="flex-1">
                            <p class="text-sm" v-if="selectedTracts.length === 0">
                                Click on the map to select census tracts
                            </p>
                            <p class="text-sm" v-else>
                                Selected and ready to save
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="flex flex-wrap gap-3">
                <button v-if="hasChanges" type="submit" class="btn btn-primary gap-2" :disabled="!isFormValid">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    {{ selectedTurf ? 'Update Turf' : 'Save Turf' }}
                </button>

                <button type="button" class="btn gap-2" @click="cancelEdit">
                    {{ hasChanges ? 'Cancel' : 'Close' }}
                </button>

                <button v-if="selectedTurf" type="button" class="btn btn-error gap-2 ml-auto" @click="deleteTurf">
                    Delete Turf
                </button>
            </div>
        </form>
    </div>
</template>

<style scoped>
.input:focus,
.textarea:focus {
    outline: none;
    border-color: hsl(var(--p));
}
</style>
