<template>
  <nav class="navigation">
    <div class="nav-container">
      <div class="nav-brand">
        <router-link to="/dashboard" class="brand-link">
          <span class="brand-icon">🏥</span>
          <span class="brand-text">MedGuard SA</span>
        </router-link>
      </div>
      
      <div class="nav-menu">
        <router-link to="/dashboard" class="nav-link">
          Dashboard
        </router-link>
        
        <router-link to="/medications" class="nav-link">
          Medications
        </router-link>
        
        <router-link v-if="isAdmin" to="/admin" class="nav-link">
          Admin
        </router-link>
      </div>
      
      <div class="nav-user">
        <div class="user-menu" @click="toggleUserMenu">
          <div class="user-avatar">
            {{ userInitials }}
          </div>
          <span class="user-name">{{ user?.name || 'User' }}</span>
          <span class="user-arrow">▼</span>
        </div>
        
        <div v-if="showUserMenu" class="user-dropdown">
          <div class="dropdown-header">
            <div class="user-info">
              <div class="user-avatar-large">{{ userInitials }}</div>
              <div class="user-details">
                <div class="user-full-name">{{ user?.name }}</div>
                <div class="user-email">{{ user?.email }}</div>
                <div class="user-type">{{ userTypeLabel }}</div>
              </div>
            </div>
          </div>
          
          <div class="dropdown-menu">
            <router-link to="/profile" class="dropdown-item">
              <span class="item-icon">👤</span>
              Profile Settings
            </router-link>
            
            <button @click="handleLogout" class="dropdown-item logout-item">
              <span class="item-icon">🚪</span>
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

const { user, logout, isAdmin } = useAuth()

const showUserMenu = ref(false)

const userInitials = computed(() => {
  if (!user.value?.name) return 'U'
  return user.value.name
    .split(' ')
    .map(name => name.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

const userTypeLabel = computed(() => {
  switch (user.value?.userType) {
    case 'PATIENT':
      return 'Patient'
    case 'CAREGIVER':
      return 'Caregiver'
    case 'HEALTHCARE_PROVIDER':
      return 'Healthcare Provider'
    default:
      return 'User'
  }
})

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleLogout = async () => {
  showUserMenu.value = false
  await logout('User initiated logout')
}

// Close menu when clicking outside
const closeMenu = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.nav-user')) {
    showUserMenu.value = false
  }
}

// Add click listener to document
document.addEventListener('click', closeMenu)
</script>

<style scoped>
.navigation {
  background: white;
  border-bottom: 1px solid #E5E7EB;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.nav-brand {
  display: flex;
  align-items: center;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: #2563EB;
  font-weight: 700;
  font-size: 1.25rem;
}

.brand-icon {
  font-size: 1.5rem;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: #374151;
  font-weight: 500;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: #2563EB;
  border-bottom-color: #2563EB;
}

.nav-link.router-link-active {
  color: #2563EB;
  border-bottom-color: #2563EB;
}

.nav-user {
  position: relative;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.user-menu:hover {
  background: #F3F4F6;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #2563EB;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
}

.user-name {
  font-weight: 500;
  color: #374151;
}

.user-arrow {
  font-size: 0.75rem;
  color: #6B7280;
  transition: transform 0.2s ease;
}

.user-menu:hover .user-arrow {
  transform: rotate(180deg);
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 280px;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  margin-top: 0.5rem;
  z-index: 1000;
}

.dropdown-header {
  padding: 1rem;
  border-bottom: 1px solid #E5E7EB;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-avatar-large {
  width: 48px;
  height: 48px;
  background: #2563EB;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1rem;
}

.user-details {
  flex: 1;
}

.user-full-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
}

.user-email {
  font-size: 0.875rem;
  color: #6B7280;
  margin-bottom: 0.25rem;
}

.user-type {
  font-size: 0.75rem;
  color: #2563EB;
  background: #EFF6FF;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}

.dropdown-menu {
  padding: 0.5rem;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 6px;
  text-decoration: none;
  color: #374151;
  font-weight: 500;
  transition: background-color 0.2s ease;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #F3F4F6;
}

.dropdown-item.logout-item {
  color: #DC2626;
}

.dropdown-item.logout-item:hover {
  background: #FEF2F2;
}

.item-icon {
  font-size: 1.125rem;
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }
  
  .user-name {
    display: none;
  }
  
  .user-dropdown {
    width: 240px;
  }
}
</style> 