<script lang="ts" setup>
import Map from '@/components/Map.vue'
import { computed, onMounted, ref, watch } from 'vue';
import { useMapStore } from '@/stores/map';
import { useTurfStore } from '@/stores/turf';
import { storeToRefs } from 'pinia';
import TurfInfo from '@/components/TurfInfo.vue';
import TurfEdit from '@/components/TurfEdit.vue';
import TurfSuggestions from '@/components/TurfSuggestions.vue';

const mapStore = useMapStore()
const turfStore = useTurfStore()
const { mode } = storeToRefs(mapStore)

onMounted(() => {
    turfStore.loadTurfs();
})

</script>

<template>
    <main>
        <div class="map-container">
            <Map></Map>
        </div>
        <div class="container">
            <div v-if="mode === 'view'">
                <TurfInfo />
            </div>
            <div v-else-if="mode === 'edit'">
                <TurfEdit />
            </div>
            <div v-else-if="mode === 'suggestion'">
                <TurfSuggestions />
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
</style>