<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

interface UserData {
  username: string
  org_name: string
  org_id: string
}

interface Record {
  id: string
  tracts: string[]
  description: {
    name: string
    details: string
  }
  org_id: string
}

const route = useRoute()
const userData = ref<UserData | null>(null)
const records = ref<Record[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const operationResult = ref<string | null>(null)

// Form fields for POST/PUT
const formMode = ref<'create' | 'edit'>('create')
const selectedRecordId = ref<string>('')
const tractInput = ref<string>('')
const tracts = ref<string[]>([])
const descriptionName = ref<string>('')
const descriptionDetails = ref<string>('')

const API_BASE_ROUTE = ref('')

const initApiRoute = () => {
  API_BASE_ROUTE.value = route.path === '/' 
    ? 'http://127.0.0.1:8000/partners/test/turf/api' 
    : './api'
}

const fetchUserData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch(API_BASE_ROUTE.value)
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

// GET - Fetch all records
const fetchRecords = async () => {
  try {
    operationResult.value = null
    const response = await fetch(`${API_BASE_ROUTE.value}/edit`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    records.value = await response.json()
    operationResult.value = `✓ Successfully fetched ${records.value.length} records`
  } catch (e) {
    operationResult.value = `✗ Error fetching records: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}

// POST - Create new record
const createRecord = async () => {
  try {
    operationResult.value = null
    const response = await fetch(`${API_BASE_ROUTE.value}/edit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tracts: tracts.value,
        description: {
          name: descriptionName.value,
          details: descriptionDetails.value
        }
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const newRecord = await response.json()
    operationResult.value = `✓ Successfully created record with ID: ${newRecord.id}`
    resetForm()
    await fetchRecords()
  } catch (e) {
    operationResult.value = `✗ Error creating record: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}

// PUT - Update existing record
const updateRecord = async () => {
  try {
    operationResult.value = null
    const response = await fetch(`${API_BASE_ROUTE.value}/edit`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: selectedRecordId.value,
        tracts: tracts.value,
        description: {
          name: descriptionName.value,
          details: descriptionDetails.value
        }
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const updatedRecord = await response.json()
    operationResult.value = `✓ Successfully updated record ID: ${updatedRecord.id}`
    resetForm()
    await fetchRecords()
  } catch (e) {
    operationResult.value = `✗ Error updating record: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}

// DELETE - Delete record
const deleteRecord = async (recordId: string) => {
  if (!confirm(`Are you sure you want to delete record ${recordId}?`)) {
    return
  }
  
  try {
    operationResult.value = null
    const response = await fetch(`${API_BASE_ROUTE.value}/edit?id=${recordId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    operationResult.value = `✓ Successfully deleted record ID: ${recordId}`
    await fetchRecords()
  } catch (e) {
    operationResult.value = `✗ Error deleting record: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}

const addTract = () => {
  if (tractInput.value.trim()) {
    tracts.value.push(tractInput.value.trim())
    tractInput.value = ''
  }
}

const removeTract = (index: number) => {
  tracts.value.splice(index, 1)
}

const loadRecordForEdit = (record: Record) => {
  formMode.value = 'edit'
  selectedRecordId.value = record.id
  tracts.value = [...record.tracts]
  descriptionName.value = record.description.name
  descriptionDetails.value = record.description.details
}

const resetForm = () => {
  formMode.value = 'create'
  selectedRecordId.value = ''
  tracts.value = []
  tractInput.value = ''
  descriptionName.value = ''
  descriptionDetails.value = ''
}

const submitForm = () => {
  if (formMode.value === 'create') {
    createRecord()
  } else {
    updateRecord()
  }
}

onMounted(() => {
  initApiRoute()
  fetchUserData()
  fetchRecords()
})
</script>

<template>
  <div>
    <h1>Turf Testing</h1>
    
    <div v-if="loading">
      <p>Loading user data...</p>
    </div>
    
    <div v-else-if="error">
      <p style="color: red;">Error: {{ error }}</p>
      <button @click="fetchUserData">Retry</button>
    </div>
    
    <div v-else-if="userData">
      <h2>User Information</h2>
      <p><strong>Username:</strong> {{ userData.username }}</p>
      <p><strong>Organization:</strong> {{ userData.org_name }}</p>
      <p><strong>Organization ID:</strong> {{ userData.org_id }}</p>
    </div>

    <div v-if="operationResult">
      <p :style="{ color: operationResult.startsWith('✓') ? 'green' : 'red' }">
        {{ operationResult }}
      </p>
    </div>

    <hr>

    <h2>{{ formMode === 'create' ? 'Create New Record (POST)' : 'Edit Record (PUT)' }}</h2>
    
    <div>
      <label>Name: <input v-model="descriptionName" type="text" /></label>
    </div>

    <div>
      <label>Details: <textarea v-model="descriptionDetails" rows="3"></textarea></label>
    </div>

    <div>
      <label>Tracts:</label>
      <input 
        v-model="tractInput" 
        type="text" 
        placeholder="Enter tract"
        @keyup.enter="addTract"
      />
      <button @click="addTract">Add Tract</button>
      
      <ul v-if="tracts.length > 0">
        <li v-for="(tract, index) in tracts" :key="index">
          {{ tract }} <button @click="removeTract(index)">Remove</button>
        </li>
      </ul>
    </div>

    <div>
      <button @click="submitForm">
        {{ formMode === 'create' ? 'Create Record' : 'Update Record' }}
      </button>
      <button v-if="formMode === 'edit'" @click="resetForm">Cancel Edit</button>
    </div>

    <hr>

    <h2>Existing Records (GET)</h2>
    <button @click="fetchRecords">Refresh Records</button>

    <div v-if="records.length === 0">
      <p>No records found.</p>
    </div>

    <div v-else>
      <div v-for="record in records" :key="record.id" style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
        <h3>{{ record.description.name || 'Untitled' }}</h3>
        <p><small>ID: {{ record.id }}</small></p>
        <p>{{ record.description.details || 'No description' }}</p>
        <p><strong>Tracts:</strong> {{ record.tracts.join(', ') }}</p>
        <button @click="loadRecordForEdit(record)">Edit</button>
        <button @click="deleteRecord(record.id)">Delete</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
input, textarea {
  margin: 5px 0;
  padding: 5px;
}

button {
  margin: 5px;
  padding: 5px 10px;
}

hr {
  margin: 20px 0;
}
</style>