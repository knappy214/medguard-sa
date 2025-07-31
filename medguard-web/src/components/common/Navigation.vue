<template>
  <nav class="navbar bg-base-100 border-b border-base-300 shadow-sm sticky top-0 z-50">
    <div class="navbar-start">
      <router-link to="/dashboard" class="btn btn-ghost text-xl">
        <Logo size="md" :show-text="false" />
        <span class="font-bold text-primary ml-2">MedGuard SA</span>
      </router-link>
    </div>
    
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li>
          <router-link to="/dashboard" class="link link-hover">
            Dashboard
          </router-link>
        </li>
        
        <li>
          <router-link to="/medications" class="link link-hover">
            Medications
          </router-link>
        </li>
        
        <li v-if="isAdmin">
          <router-link to="/admin" class="link link-hover">
            Admin
          </router-link>
        </li>
      </ul>
    </div>
    
    <div class="navbar-end">
      <div class="flex items-center gap-2">
        <!-- Language Switcher -->
        <LanguageSwitcher />
        
        <!-- Theme Toggle -->
        <ThemeToggle />
        
        <!-- User Menu -->
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
            <Avatar 
              :src="user?.avatarUrl"
              :name="user?.name"
              :email="user?.email"
              size="sm"
              alt="User avatar"
            />
          </div>
          <ul tabindex="0" class="dropdown-content menu menu-sm z-[1] mt-3 w-64 bg-base-100 rounded-box shadow-lg border border-base-300">
            <li class="menu-title">
              <div class="flex items-center gap-3 p-3">
                <Avatar 
                  :src="user?.avatarUrl"
                  :name="user?.name"
                  :email="user?.email"
                  size="md"
                  alt="User avatar"
                />
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-base truncate">{{ user?.name }}</div>
                  <div class="text-sm opacity-70 truncate">{{ user?.email }}</div>
                  <div class="badge badge-primary badge-sm mt-1">{{ userTypeLabel }}</div>
                </div>
              </div>
            </li>
            <div class="divider my-1"></div>
            <li>
              <router-link to="/profile" class="flex items-center gap-3 p-3 hover:bg-base-200 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>Profile Settings</span>
              </router-link>
            </li>
            <li>
              <button @click="handleLogout" class="flex items-center gap-3 p-3 text-error hover:bg-error hover:text-error-content transition-colors w-full text-left">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span>Sign Out</span>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ThemeToggle from './ThemeToggle.vue'
import Logo from './Logo.vue'
import Avatar from './Avatar.vue'

const { user, logout, isAdmin } = useAuth()

// Debug logging for user data
console.log('Navigation: Current user data:', user.value)
console.log('Navigation: User avatarUrl:', user.value?.avatarUrl)

// Watch for changes in user data
watch(() => user.value, (newUser, oldUser) => {
  console.log('Navigation: User data changed:', {
    oldAvatarUrl: oldUser?.avatarUrl,
    newAvatarUrl: newUser?.avatarUrl,
    oldUser: oldUser,
    newUser: newUser
  })
}, { deep: true })

// Watch specifically for avatarUrl changes
watch(() => user.value?.avatarUrl, (newAvatarUrl, oldAvatarUrl) => {
  console.log('Navigation: Avatar URL changed:', {
    from: oldAvatarUrl,
    to: newAvatarUrl
  })
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

const handleLogout = async () => {
  await logout('User initiated logout')
}
</script>

 