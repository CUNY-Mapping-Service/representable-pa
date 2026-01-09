<script lang="ts" setup>
import Map from '@/components/Map.vue'

</script>

<template>
    <main>
        <div class="map-container">
            <Map></Map>
        </div>
        <div class="container"></div>
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