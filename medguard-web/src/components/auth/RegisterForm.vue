<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h2>🏥 MedGuard SA</h2>
        <p>Create Your Healthcare Account</p>
      </div>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <!-- Personal Information -->
        <div class="form-section">
          <h3>Personal Information</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label for="firstName">First Name</label>
              <input
                id="firstName"
                v-model="formData.first_name"
                type="text"
                required
                placeholder="Enter your first name"
                class="form-input"
              />
            </div>
            
            <div class="form-group">
              <label for="lastName">Last Name</label>
              <input
                id="lastName"
                v-model="formData.last_name"
                type="text"
                required
                placeholder="Enter your last name"
                class="form-input"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label for="email">Email Address</label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              placeholder="Enter your email address"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="username">Username</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              required
              placeholder="Choose a username"
              class="form-input"
            />
          </div>
        </div>
        
        <!-- Account Type -->
        <div class="form-section">
          <h3>Account Type</h3>
          
          <div class="form-group">
            <label for="userType">I am a:</label>
            <select
              id="userType"
              v-model="formData.user_type"
              required
              class="form-select"
            >
              <option value="">Select your role</option>
              <option value="patient">Patient</option>
              <option value="caregiver">Caregiver</option>
              <option value="healthcare_provider">Healthcare Provider</option>
            </select>
          </div>
        </div>
        
        <!-- Security -->
        <div class="form-section">
          <h3>Security</h3>
          
          <div class="form-group">
            <label for="password">Password</label>
            <div class="password-input-container">
              <input
                id="password"
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="Create a strong password"
                class="form-input"
                @input="validatePassword"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
            <div class="password-strength" v-if="formData.password">
              <div class="strength-bar">
                <div 
                  class="strength-fill" 
                  :class="passwordStrength.class"
                  :style="{ width: passwordStrength.percentage + '%' }"
                ></div>
              </div>
              <span class="strength-text" :class="passwordStrength.class">
                {{ passwordStrength.text }}
              </span>
            </div>
          </div>
          
          <div class="form-group">
            <label for="passwordConfirm">Confirm Password</label>
            <input
              id="passwordConfirm"
              v-model="formData.password_confirm"
              type="password"
              required
              placeholder="Confirm your password"
              class="form-input"
              @input="validatePasswordMatch"
            />
            <div v-if="formData.password_confirm && !passwordsMatch" class="error-text">
              Passwords do not match
            </div>
          </div>
        </div>
        
        <!-- Terms and Conditions -->
        <div class="form-section">
          <div class="form-group">
            <label class="checkbox-label">
              <input
                v-model="formData.acceptTerms"
                type="checkbox"
                required
                class="checkbox-input"
              />
              <span class="checkbox-text">
                I agree to the 
                <a href="#" @click.prevent="showTerms = true" class="link">Terms of Service</a>
                and 
                <a href="#" @click.prevent="showPrivacy = true" class="link">Privacy Policy</a>
              </span>
            </label>
          </div>
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button 
          type="submit" 
          :disabled="loading || !isFormValid"
          class="register-button"
        >
          <span v-if="loading">Creating Account...</span>
          <span v-else>Create Account</span>
        </button>
      </form>
      
      <div class="register-footer">
        <p>Already have an account? <a href="#" @click.prevent="goToLogin" class="link">Sign In</a></p>
      </div>
    </div>
    
    <!-- Terms Modal -->
    <div v-if="showTerms" class="modal-overlay" @click="showTerms = false">
      <div class="modal" @click.stop>
        <h3>Terms of Service</h3>
        <div class="modal-content">
          <p>By using MedGuard SA, you agree to comply with all applicable healthcare regulations including HIPAA and POPIA.</p>
          <p>You are responsible for maintaining the confidentiality of your account and for all activities that occur under your account.</p>
          <p>MedGuard SA is designed for healthcare professionals and patients to manage medication schedules securely.</p>
        </div>
        <button @click="showTerms = false" class="modal-close">Close</button>
      </div>
    </div>
    
    <!-- Privacy Modal -->
    <div v-if="showPrivacy" class="modal-overlay" @click="showPrivacy = false">
      <div class="modal" @click.stop>
        <h3>Privacy Policy</h3>
        <div class="modal-content">
          <p>Your health information is protected under strict privacy regulations.</p>
          <p>We use industry-standard encryption to protect your data both in transit and at rest.</p>
          <p>We do not share your personal health information with third parties without your explicit consent.</p>
        </div>
        <button @click="showPrivacy = false" class="modal-close">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import authService from '@/services/authService'

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

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2563EB, #10B981);
  padding: 1rem;
}

.register-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.register-header {
  text-align: center;
  margin-bottom: 2rem;
}

.register-header h2 {
  color: #2563EB;
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.register-header p {
  color: #6B7280;
  margin: 0;
  font-size: 0.875rem;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-section {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 1.5rem;
}

.form-section h3 {
  color: #374151;
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
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

.password-input-container {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.strength-fill.weak {
  background: #EF4444;
}

.strength-fill.fair {
  background: #F59E0B;
}

.strength-fill.strong {
  background: #10B981;
}

.strength-text {
  font-size: 0.75rem;
  font-weight: 500;
}

.strength-text.weak {
  color: #EF4444;
}

.strength-text.fair {
  color: #F59E0B;
}

.strength-text.strong {
  color: #10B981;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-input {
  margin-top: 0.125rem;
}

.checkbox-text {
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.4;
}

.link {
  color: #2563EB;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.register-button {
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

.register-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.register-button:disabled {
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

.error-text {
  color: #DC2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.register-footer {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #E5E7EB;
}

.register-footer p {
  color: #6B7280;
  font-size: 0.875rem;
  margin: 0;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  color: #374151;
  margin: 0 0 1rem 0;
}

.modal-content {
  margin-bottom: 1.5rem;
}

.modal-content p {
  color: #6B7280;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.modal-close {
  background: #2563EB;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .register-card {
    padding: 1.5rem;
  }
}
</style> 