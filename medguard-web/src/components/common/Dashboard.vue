<template>
  <div class="container mx-auto p-8">
    <div class="flex justify-between items-center mb-8 pb-4 border-b border-base-300">
      <div class="flex items-center gap-4">
        <Logo size="lg" :show-text="false" />
        <h1 class="text-4xl font-bold text-primary">MedGuard SA Dashboard</h1>
      </div>
      <div class="flex items-center gap-4">
        <span v-if="isAuthenticated" class="text-base-content">
          Welcome, {{ currentUser?.name || 'User' }}!
        </span>
        <button @click="handleLogout" class="btn btn-error btn-outline">
          Logout
        </button>
      </div>
    </div>

    <div v-if="isAuthenticated" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl">User Information</h2>
          <div class="space-y-2">
            <p><strong>ID:</strong> {{ currentUser?.id }}</p>
            <p><strong>Email:</strong> {{ currentUser?.email }}</p>
            <p><strong>Name:</strong> {{ currentUser?.name }}</p>
            <p><strong>User Type:</strong> {{ currentUser?.userType }}</p>
            <p><strong>Last Login:</strong> {{ formatDate(currentUser?.lastLogin) }}</p>
            <p><strong>MFA Enabled:</strong> {{ currentUser?.mfaEnabled ? 'Yes' : 'No' }}</p>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl">Permissions</h2>
          <div class="flex flex-wrap gap-2">
            <span 
              v-for="permission in currentUser?.permissions" 
              :key="permission"
              class="badge badge-primary"
            >
              {{ permission }}
            </span>
          </div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-lg">
        <div class="card-body">
          <h2 class="card-title text-xl">Security Information</h2>
          <div class="space-y-2">
            <p><strong>Device ID:</strong> {{ securitySettings.deviceId }}</p>
            <p><strong>Session Timeout:</strong> {{ formatDuration(securitySettings.sessionTimeout) }}</p>
            <p><strong>Last Activity:</strong> {{ formatDate(securitySettings.lastActivity) }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="card bg-base-100 shadow-lg">
      <div class="card-body text-center py-16">
        <p class="text-lg text-base-content/70 mb-4">Please log in to access the dashboard.</p>
        <router-link to="/login" class="btn btn-primary">
          Go to Login
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import authService from '@/services/authService'
import Logo from '@/components/common/Logo.vue'

const router = useRouter()

// Create computed properties to properly access auth service data
const currentUser = computed(() => authService.currentUser.value)
const isAuthenticated = computed(() => authService.authenticated.value)
const securitySettings = computed(() => authService.getSecuritySettings())

const handleLogout = async () => {
  try {
    await authService.logout('User initiated logout')
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return 'Invalid Date'
  }
}

const formatDuration = (milliseconds: number) => {
  const minutes = Math.floor(milliseconds / (1000 * 60))
  return `${minutes} minutes`
}

onMounted(() => {
  // Check if user is already authenticated
  if (!isAuthenticated.value) {
    console.log('User not authenticated, redirecting to login')
    router.push('/login')
  }
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #E5E7EB;
}

.dashboard-header h1 {
  color: #2563EB;
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-button {
  background: #EF4444;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.logout-button:hover {
  background: #DC2626;
}

.dashboard-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.user-card,
.permissions-card,
.security-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #E5E7EB;
}

.user-card h2,
.permissions-card h2,
.security-card h2 {
  color: #374151;
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.user-details p,
.security-details p {
  margin: 0.5rem 0;
  color: #6B7280;
}

.user-details strong,
.security-details strong {
  color: #374151;
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.permission-tag {
  background: #DBEAFE;
  color: #1E40AF;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

.login-prompt {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.login-prompt p {
  color: #6B7280;
  margin-bottom: 1rem;
  font-size: 1.125rem;
}

.login-link {
  display: inline-block;
  background: #2563EB;
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.login-link:hover {
  background: #1D4ED8;
}
</style> 