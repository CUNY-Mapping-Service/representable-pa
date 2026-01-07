<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

interface UserData {
  username: string
  org_name: string
  org_id: string
}

const route = useRoute()
const userData = ref<UserData | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const fetchUserData = async () => {
  try {
    loading.value = true
    error.value = null

    // dev should use the full route, prod should use relative 
    const API_BASE_ROUTE = route.path === '/' ? 'http://127.0.0.1:8000/partners/test/turf/api' : './api'
   
    const response = await fetch(API_BASE_ROUTE)

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const text = await response.text()

    if (!text) {
      throw new Error('Empty response from server')
    }

    userData.value = JSON.parse(text)

  } catch (e) {
    error.value = e instanceof Error ? e.message : 'An error occurred'
    console.error('Error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUserData()
})
</script>

<template>
  <div>
    <h1>You did it!</h1>

    <div v-if="loading">
      <p>Loading...</p>
    </div>

    <div v-else-if="error">
      <p style="color: red;">Error: {{ error }}</p>
      <button @click="fetchUserData">Retry</button>
    </div>

    <div v-else-if="userData">
      <h2>User Information</h2>
      <p><strong>Username:</strong> {{ userData.username }}</p>
      <p><strong>Organization Name:</strong> {{ userData.org_name }}</p>
      <p><strong>Organization ID:</strong> {{ userData.org_id }}</p>
    </div>

    <p>
      Visit <a href="https://vuejs.org/" target="_blank" rel="noopener">vuejs.org</a> to read the
      documentation
    </p>
  </div>
</template>

<style scoped>
h2 {
  margin-top: 20px;
}

</style>