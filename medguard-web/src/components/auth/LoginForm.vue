<template>
  <div class="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
    <div class="card w-full max-w-md bg-base-100 shadow-xl">
      <div class="card-body">
        <div class="text-center mb-6">
          <div class="flex justify-center mb-4">
            <Logo size="lg" :show-text="false" />
          </div>
          <h2 class="text-3xl font-bold text-primary">MedGuard SA</h2>
          <p class="text-base-content/70 mt-2">Professional Healthcare Management System</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div class="form-control">
            <label for="username_or_email" class="label">
              <span class="label-text font-medium">Username or Email</span>
            </label>
            <input
              id="username_or_email"
              v-model="formData.username_or_email"
              type="text"
              required
              autocomplete="username"
              placeholder="Enter your username or email"
              class="input input-bordered w-full focus:input-primary"
            />
          </div>
          
          <div class="form-control">
            <label for="password" class="label">
              <span class="label-text font-medium">Password</span>
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="Enter your password"
                class="input input-bordered w-full pr-12 focus:input-primary"
              />
              <button
                type="button"
                @click="togglePassword"
                class="btn btn-ghost absolute right-0 top-0 h-full px-3"
              >
                <svg v-if="showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
          </div>
          
          <div class="flex items-center justify-between">
            <label class="label cursor-pointer">
              <input
                v-model="formData.remember_me"
                type="checkbox"
                class="checkbox checkbox-primary"
              />
              <span class="label-text ml-2">Remember me</span>
            </label>
            <router-link to="/password-reset" class="link link-primary text-sm">
              Forgot password?
            </router-link>
          </div>
          
          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary w-full"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
          
          <div v-if="error" class="alert alert-error">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ error }}</span>
          </div>
        </form>
        
        <div class="text-center mt-6 pt-6 border-t border-base-300">
          <p class="text-base-content/70">
            Don't have an account?
            <router-link to="/register" class="link link-primary font-medium">
              Sign up here
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import authService from '@/services/authService'
import Logo from '@/components/common/Logo.vue'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const formData = reactive({
  username_or_email: '',
  password: '',
  remember_me: false
})

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const user = await authService.login({
      email: formData.username_or_email,
      password: formData.password
    })
    
    // Store remember me preference
    if (formData.remember_me) {
      localStorage.setItem('medguard_remember_me', 'true')
    } else {
      localStorage.removeItem('medguard_remember_me')
    }
    
    // Redirect to dashboard
    router.push('/dashboard')
  } catch (err) {
    console.error('Login failed:', err)
    error.value = err instanceof Error ? err.message : 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

 