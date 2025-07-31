<template>
  <div class="profile-container">
    <div class="profile-card">
      <div class="profile-header">
        <h2>👤 Profile Settings</h2>
        <p>Manage your account information</p>
      </div>
      
      <form @submit.prevent="handleUpdateProfile" class="profile-form">
        <div class="form-row">
          <div class="form-group">
            <label for="firstName">First Name</label>
            <input
              id="firstName"
              v-model="profileData.first_name"
              type="text"
              required
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="lastName">Last Name</label>
            <input
              id="lastName"
              v-model="profileData.last_name"
              type="text"
              required
              class="form-input"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            v-model="profileData.email"
            type="email"
            required
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="language">Preferred Language</label>
          <select v-model="profileData.preferred_language" class="form-select">
            <option value="en">English</option>
            <option value="af">Afrikaans</option>
          </select>
        </div>
        
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>
        
        <button type="submit" :disabled="loading" class="update-button">
          {{ loading ? 'Updating...' : 'Update Profile' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import authService from '@/services/authService'

const loading = ref(false)
const error = ref('')
const success = ref('')

const profileData = reactive({
  first_name: '',
  last_name: '',
  email: '',
  preferred_language: 'en'
})

const loadProfile = async () => {
  try {
    const response = await fetch('/api/users/profile/', {
      headers: {
        'Authorization': `Bearer ${await authService.getAccessToken()}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      Object.assign(profileData, data)
    }
  } catch (err) {
    console.error('Failed to load profile:', err)
  }
}

const handleUpdateProfile = async () => {
  try {
    loading.value = true
    error.value = ''
    success.value = ''
    
    const response = await fetch('/api/users/profile/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await authService.getAccessToken()}`
      },
      body: JSON.stringify(profileData)
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to update profile')
    }
    
    success.value = 'Profile updated successfully'
    
  } catch (err) {
    console.error('Profile update failed:', err)
    error.value = err instanceof Error ? err.message : 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  padding: 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.profile-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.profile-header {
  text-align: center;
  margin-bottom: 2rem;
}

.profile-header h2 {
  color: #2563EB;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.profile-header p {
  color: #6B7280;
  margin: 0;
  font-size: 0.875rem;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-input,
.form-select {
  padding: 0.75rem;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.update-button {
  background: #2563EB;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.update-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.update-button:disabled {
  background: #9CA3AF;
  cursor: not-allowed;
}

.error-message {
  background: #FEF2F2;
  color: #DC2626;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  border: 1px solid #FECACA;
}

.success-message {
  background: #F0FDF4;
  color: #16A34A;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  border: 1px solid #BBF7D0;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style> 