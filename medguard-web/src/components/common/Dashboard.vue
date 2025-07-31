<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>🏥 MedGuard SA Dashboard</h1>
      <div class="user-info">
        <span v-if="authService.authenticated">
          Welcome, {{ authService.currentUser?.name || 'User' }}!
        </span>
        <button @click="handleLogout" class="logout-button">
          Logout
        </button>
      </div>
    </div>

    <div v-if="authService.authenticated" class="dashboard-content">
      <div class="user-card">
        <h2>User Information</h2>
        <div class="user-details">
          <p><strong>ID:</strong> {{ authService.currentUser?.id }}</p>
          <p><strong>Email:</strong> {{ authService.currentUser?.email }}</p>
          <p><strong>Name:</strong> {{ authService.currentUser?.name }}</p>
          <p><strong>User Type:</strong> {{ authService.currentUser?.userType }}</p>
          <p><strong>Last Login:</strong> {{ formatDate(authService.currentUser?.lastLogin) }}</p>
          <p><strong>MFA Enabled:</strong> {{ authService.currentUser?.mfaEnabled ? 'Yes' : 'No' }}</p>
        </div>
      </div>

      <div class="permissions-card">
        <h2>Permissions</h2>
        <div class="permissions-list">
          <span 
            v-for="permission in authService.currentUser?.permissions" 
            :key="permission"
            class="permission-tag"
          >
            {{ permission }}
          </span>
        </div>
      </div>

      <div class="security-card">
        <h2>Security Information</h2>
        <div class="security-details">
          <p><strong>Device ID:</strong> {{ securitySettings.deviceId }}</p>
          <p><strong>Session Timeout:</strong> {{ formatDuration(securitySettings.sessionTimeout) }}</p>
          <p><strong>Last Activity:</strong> {{ formatDate(securitySettings.lastActivity) }}</p>
        </div>
      </div>
    </div>

    <div v-else class="login-prompt">
      <p>Please log in to access the dashboard.</p>
      <router-link to="/login" class="login-link">
        Go to Login
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import authService from '@/services/authService'

const router = useRouter()

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
  if (!authService.authenticated.value) {
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