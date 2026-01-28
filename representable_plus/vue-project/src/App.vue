<script setup lang="ts">
import { RouterView } from 'vue-router'
import './app.css'

</script>

<template>
    <!-- <header>
        <nav>
            <RouterLink to="/">🏠</RouterLink>
        </nav>
    </header> -->

    <RouterView />

</template>

<style scoped>
header {
    position: relative;
    z-index: 99;
}

nav {
    position: absolute;
    left: 0;
}
</style>