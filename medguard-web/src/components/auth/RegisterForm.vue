<template>
  <div class="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
    <div class="card w-full max-w-2xl bg-base-100 shadow-xl max-h-[90vh] overflow-y-auto">
      <div class="card-body">
        <div class="text-center mb-6">
          <div class="flex justify-center mb-4">
            <Logo size="lg" :show-text="false" />
          </div>
          <h2 class="text-3xl font-bold text-primary">MedGuard SA</h2>
          <p class="text-base-content/70 mt-2">Create Your Healthcare Account</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="space-y-8">
          <!-- Personal Information -->
          <div class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">Personal Information</h3>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-control">
                  <label for="firstName" class="label">
                    <span class="label-text font-medium">First Name</span>
                  </label>
                  <input
                    id="firstName"
                    v-model="formData.first_name"
                    type="text"
                    required
                    autocomplete="given-name"
                    placeholder="Enter your first name"
                    class="input input-bordered w-full focus:input-primary"
                  />
                </div>
                
                <div class="form-control">
                  <label for="lastName" class="label">
                    <span class="label-text font-medium">Last Name</span>
                  </label>
                  <input
                    id="lastName"
                    v-model="formData.last_name"
                    type="text"
                    required
                    autocomplete="family-name"
                    placeholder="Enter your last name"
                    class="input input-bordered w-full focus:input-primary"
                  />
                </div>
              </div>
              
              <div class="form-control">
                <label for="email" class="label">
                  <span class="label-text font-medium">Email Address</span>
                </label>
                <input
                  id="email"
                  v-model="formData.email"
                  type="email"
                  required
                  autocomplete="email"
                  placeholder="Enter your email address"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
              
              <div class="form-control">
                <label for="username" class="label">
                  <span class="label-text font-medium">Username</span>
                </label>
                <input
                  id="username"
                  v-model="formData.username"
                  type="text"
                  required
                  autocomplete="username"
                  placeholder="Choose a username"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>
          </div>
          
          <!-- Account Type -->
          <div class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">Account Type</h3>
              
              <div class="form-control">
                <label for="userType" class="label">
                  <span class="label-text font-medium">I am a:</span>
                </label>
                <select
                  id="userType"
                  v-model="formData.user_type"
                  required
                  class="select select-bordered w-full focus:select-primary"
                >
                  <option value="">Select your role</option>
                  <option value="patient">Patient</option>
                  <option value="caregiver">Caregiver</option>
                  <option value="healthcare_provider">Healthcare Provider</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Security -->
          <div class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">Security</h3>
              
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
                    autocomplete="new-password"
                    placeholder="Create a strong password"
                    class="input input-bordered w-full pr-12 focus:input-primary"
                    @input="validatePassword"
                  />
                  <button
                    type="button"
                    class="btn btn-ghost btn-sm absolute right-2 top-1/2 transform -translate-y-1/2"
                    @click="showPassword = !showPassword"
                  >
                    {{ showPassword ? '👁️' : '👁️‍🗨️' }}
                  </button>
                </div>
                <div class="password-strength mt-2" v-if="formData.password">
                  <div class="flex items-center gap-2">
                    <progress 
                      class="progress flex-1" 
                      :class="passwordStrength.class === 'weak' ? 'progress-error' : passwordStrength.class === 'fair' ? 'progress-warning' : 'progress-success'"
                      :value="passwordStrength.percentage" 
                      max="100"
                    ></progress>
                    <span class="text-sm font-medium" :class="passwordStrength.class === 'weak' ? 'text-error' : passwordStrength.class === 'fair' ? 'text-warning' : 'text-success'">
                      {{ passwordStrength.text }}
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="form-control">
                <label for="passwordConfirm" class="label">
                  <span class="label-text font-medium">Confirm Password</span>
                </label>
                                  <input
                    id="passwordConfirm"
                    v-model="formData.password_confirm"
                    type="password"
                    required
                    autocomplete="new-password"
                    placeholder="Confirm your password"
                    class="input input-bordered w-full focus:input-primary"
                    @input="validatePasswordMatch"
                  />
                <div v-if="formData.password_confirm && !passwordsMatch" class="label">
                  <span class="label-text-alt text-error">Passwords do not match</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Terms and Conditions -->
          <div class="card bg-base-200">
            <div class="card-body">
              <div class="form-control">
                <label class="label cursor-pointer">
                  <input
                    v-model="formData.acceptTerms"
                    type="checkbox"
                    required
                    class="checkbox checkbox-primary"
                  />
                  <span class="label-text ml-2">
                    I agree to the 
                    <a href="#" @click.prevent="showTerms = true" class="link link-primary">Terms of Service</a>
                    and 
                    <a href="#" @click.prevent="showPrivacy = true" class="link link-primary">Privacy Policy</a>
                  </span>
                </label>
              </div>
            </div>
          </div>
          
          <div v-if="error" class="alert alert-error">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ error }}</span>
          </div>
          
          <button 
            type="submit" 
            :disabled="loading || !isFormValid"
            class="btn btn-primary w-full"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            <span v-if="loading">Creating Account...</span>
            <span v-else>Create Account</span>
          </button>
        </form>
        
        <div class="text-center mt-6 pt-6 border-t border-base-300">
          <p class="text-base-content/70 text-sm">
            Already have an account? 
            <a href="#" @click.prevent="goToLogin" class="link link-primary font-medium">Sign In</a>
          </p>
        </div>
      </div>
    </div>
    
    <!-- Terms Modal -->
    <div v-if="showTerms" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Terms of Service</h3>
        <div class="py-4 space-y-4">
          <p>By using MedGuard SA, you agree to comply with all applicable healthcare regulations including HIPAA and POPIA.</p>
          <p>You are responsible for maintaining the confidentiality of your account and for all activities that occur under your account.</p>
          <p>MedGuard SA is designed for healthcare professionals and patients to manage medication schedules securely.</p>
        </div>
        <div class="modal-action">
          <button @click="showTerms = false" class="btn btn-primary">Close</button>
        </div>
      </div>
      <div class="modal-backdrop" @click="showTerms = false"></div>
    </div>
    
    <!-- Privacy Modal -->
    <div v-if="showPrivacy" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Privacy Policy</h3>
        <div class="py-4 space-y-4">
          <p>Your health information is protected under strict privacy regulations.</p>
          <p>We use industry-standard encryption to protect your data both in transit and at rest.</p>
          <p>We do not share your personal health information with third parties without your explicit consent.</p>
        </div>
        <div class="modal-action">
          <button @click="showPrivacy = false" class="btn btn-primary">Close</button>
        </div>
      </div>
      <div class="modal-backdrop" @click="showPrivacy = false"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import authService from '@/services/authService'
import Logo from '@/components/common/Logo.vue'

const router = useRouter()

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showTerms = ref(false)
const showPrivacy = ref(false)
const passwordsMatch = ref(true)

const formData = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  password_confirm: '',
  user_type: '',
  acceptTerms: false
})

const passwordStrength = ref({
  score: 0,
  percentage: 0,
  text: '',
  class: ''
})

const validatePassword = () => {
  const password = formData.password
  let score = 0
  
  if (password.length >= 8) score += 25
  if (/[a-z]/.test(password)) score += 25
  if (/[A-Z]/.test(password)) score += 25
  if (/[0-9]/.test(password)) score += 25
  
  passwordStrength.value.score = score
  passwordStrength.value.percentage = score
  
  if (score < 50) {
    passwordStrength.value.text = 'Weak'
    passwordStrength.value.class = 'weak'
  } else if (score < 75) {
    passwordStrength.value.text = 'Fair'
    passwordStrength.value.class = 'fair'
  } else {
    passwordStrength.value.text = 'Strong'
    passwordStrength.value.class = 'strong'
  }
}

const validatePasswordMatch = () => {
  passwordsMatch.value = formData.password === formData.password_confirm
}

const isFormValid = computed(() => {
  return (
    formData.username &&
    formData.email &&
    formData.first_name &&
    formData.last_name &&
    formData.password &&
    formData.password_confirm &&
    formData.user_type &&
    formData.acceptTerms &&
    passwordsMatch.value &&
    passwordStrength.value.score >= 50
  )
})

const handleRegister = async () => {
  try {
    loading.value = true
    error.value = ''
    
    // Validate form
    if (!isFormValid.value) {
      error.value = 'Please fill in all required fields correctly'
      return
    }
    
    // Call registration endpoint using axios (which respects Vite proxy)
    const response = await axios.post('/api/users/auth/register/', formData, {
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    const data = response.data
    
    // Login the user automatically
    await authService.login({
      email: formData.email,
      password: formData.password
    })
    
    // Redirect to dashboard
    router.push('/dashboard')
    
  } catch (err) {
    console.error('Registration failed:', err)
    error.value = err instanceof Error ? err.message : 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

 