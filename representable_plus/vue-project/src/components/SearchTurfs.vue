<template>
    <div class="dropdown-container">
        <div class="custom-dropdown" v-click-outside="closeDropdown">
            <div class="dropdown-trigger" @click="toggleDropdown">
                <div class="selected-item">
                    <span class="text">{{ currentSelection.name }}</span>
                    <span class="arrow" :class="{ 'is-open': isOpen }">▼</span>
                </div>
            </div>

            <transition name="dropdown">
                <div v-if="isOpen" class="dropdown-menu">
                    <div class="search-box">
                        <input v-model="searchQuery" type="text" placeholder="Search turfs..." class="search-input"
                            @input="onSearch" ref="searchInput" />
                    </div>

                    <div class="dropdown-content">
                        <div v-for="turf in filteredTurfs" :key="turf.id" class="dropdown-item"
                            :class="{ 'is-active': selectedTurf?.id === turf.id }"
                            @click="selectTurf(turf as TurfWithColors)">
                            <div class="turf-info">
                                <span class="text">{{ turf.name }}</span>
                                <span class="turf-meta" v-if="turf.id">
                                    {{ turf.tracts?.length || 0 }} tract(s)
                                </span>
                            </div>
                        </div>

                        <div v-if="filteredTurfs.length === 0" class="dropdown-item no-results">
                            <span class="text">No turfs found</span>
                        </div>
                    </div>
                </div>
            </transition>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useTurfStore, type Turf } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import type { TurfWithColors } from '@/views/Landing.vue';

const isOpen = ref(false);
const searchQuery = ref('');
const searchInput = ref<HTMLInputElement | null>(null);

const turfStore = useTurfStore();
const { sortedTurfs, selectedTurf } = storeToRefs(turfStore);

const emptyOption = { id: 'none', name: 'Select a turf', description: '', tracts: [], createdAt: '' };

const currentSelection = computed(() => {
    return selectedTurf.value || emptyOption;
});

const availableTurfs = computed(() => {
    return sortedTurfs.value;
});

const filteredTurfs = ref<typeof availableTurfs.value>([]);

onMounted(() => {
    turfStore.loadTurfs();
    filteredTurfs.value = availableTurfs.value;
});

function toggleDropdown() {
    isOpen.value = !isOpen.value;
    if (isOpen.value) {
        // Reload turfs when opening dropdown to get latest data
        turfStore.loadTurfs();
        filteredTurfs.value = availableTurfs.value;

        setTimeout(() => {
            searchInput.value?.focus();
        }, 100);
    }
}

function closeDropdown() {
    isOpen.value = false;
    searchQuery.value = '';
    filteredTurfs.value = availableTurfs.value;
}

function selectTurf(turf: Turf | typeof emptyOption) {
    if (turf.id === 'none') {
        turfStore.clearSelectedTurf();
    } else {
        turfStore.selectTurf(turf as Turf);
    }
    closeDropdown();
}

function onSearch() {
    const query = searchQuery.value.toLowerCase();
    filteredTurfs.value = availableTurfs.value.filter(turf =>
        turf.name.toLowerCase().includes(query) ||
        turf.details?.toLowerCase().includes(query)
    );
}
</script>

<style scoped>
.title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.subtitle {
    font-size: 0.875rem;
    color: #4a5568;
    margin-bottom: 16px;
}

.custom-dropdown {
    position: relative;
}

.dropdown-trigger {
    cursor: pointer;
}

.selected-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: white;
    border: 1px solid #dbdbdb;
    border-radius: 4px;
    transition: border-color 0.2s;
}

.selected-item:hover {
    border-color: #b5b5b5;
}

.text {
    flex: 1;
    font-size: 14px;
}

.arrow {
    font-size: 10px;
    color: #7a7a7a;
    transition: transform 0.2s;
}

.arrow.is-open {
    transform: rotate(180deg);
}

.dropdown-menu {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #dbdbdb;
    border-radius: 4px;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    max-height: 320px;
    display: flex;
    flex-direction: column;
}

.search-box {
    padding: 10px;
    border-bottom: 1px solid #f0f0f0;
}

.search-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #dbdbdb;
    border-radius: 4px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}

.search-input:focus {
    border-color: #3273dc;
}

.dropdown-content {
    overflow-y: auto;
    max-height: 250px;
}

.dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.dropdown-item:hover {
    background-color: #f5f5f5;
}

.dropdown-item.is-active {
    background-color: #3273dc;
    color: white;
}

.dropdown-item.is-active .turf-meta {
    color: rgba(255, 255, 255, 0.9);
}

.dropdown-item.no-results {
    color: #7a7a7a;
    cursor: default;
}

.dropdown-item.no-results:hover {
    background-color: transparent;
}

.turf-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.turf-meta {
    font-size: 12px;
    color: #7a7a7a;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
    transition: opacity 0.2s, transform 0.2s;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

/* Scrollbar styling */
.dropdown-content::-webkit-scrollbar {
    width: 6px;
}

.dropdown-content::-webkit-scrollbar-track {
    background: #f1f1f1;
}

.dropdown-content::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.dropdown-content::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>