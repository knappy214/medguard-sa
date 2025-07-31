<template>
  <div class="reset-container">
    <div class="reset-card">
      <div class="reset-header">
        <h2>🔐 Password Reset</h2>
        <p>{{ isRequestStep ? 'Enter your email to reset your password' : 'Enter your new password' }}</p>
      </div>
      
      <!-- Step 1: Request Password Reset -->
      <form v-if="isRequestStep" @submit.prevent="handleRequestReset" class="reset-form">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            placeholder="Enter your email address"
            class="form-input"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          {{ success }}
        </div>
        
        <button 
          type="submit" 
          :disabled="loading"
          class="reset-button"
        >
          <span v-if="loading">Sending...</span>
          <span v-else>Send Reset Link</span>
        </button>
      </form>
      
      <!-- Step 2: Confirm Password Reset -->
      <form v-else @submit.prevent="handleConfirmReset" class="reset-form">
        <div class="form-group">
          <label for="newPassword">New Password</label>
          <div class="password-input-container">
            <input
              id="newPassword"
              v-model="newPassword"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder="Enter your new password"
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
          <div class="password-strength" v-if="newPassword">
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
          <label for="confirmPassword">Confirm New Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your new password"
            class="form-input"
            @input="validatePasswordMatch"
          />
          <div v-if="confirmPassword && !passwordsMatch" class="error-text">
            Passwords do not match
          </div>
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button 
          type="submit" 
          :disabled="loading || !isFormValid"
          class="reset-button"
        >
          <span v-if="loading">Resetting...</span>
          <span v-else>Reset Password</span>
        </button>
      </form>
      
      <div class="reset-footer">
        <p>
          <a href="#" @click.prevent="goToLogin" class="link">Back to Login</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref('')
const success = ref('')
const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const passwordsMatch = ref(true)

const passwordStrength = ref({
  score: 0,
  percentage: 0,
  text: '',
  class: ''
})

// Check if we're in confirmation step (has token and uid)
const isRequestStep = computed(() => {
  return !route.params.uidb64 || !route.params.token
})

const validatePassword = () => {
  const password = newPassword.value
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
  passwordsMatch.value = newPassword.value === confirmPassword.value
}

const isFormValid = computed(() => {
  if (isRequestStep.value) {
    return email.value && email.value.includes('@')
  } else {
    return (
      newPassword.value &&
      confirmPassword.value &&
      passwordsMatch.value &&
      passwordStrength.value.score >= 50
    )
  }
})

const handleRequestReset = async () => {
  try {
    loading.value = true
    error.value = ''
    success.value = ''
    
    const response = await fetch('/api/users/password-reset-request/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email.value })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to send reset link')
    }
    
    success.value = data.message || 'Password reset link sent to your email'
    
  } catch (err) {
    console.error('Password reset request failed:', err)
    error.value = err instanceof Error ? err.message : 'Failed to send reset link. Please try again.'
  } finally {
    loading.value = false
  }
}

const handleConfirmReset = async () => {
  try {
    loading.value = true
    error.value = ''
    
    if (!isFormValid.value) {
      error.value = 'Please fill in all fields correctly'
      return
    }
    
    const response = await fetch(`/api/users/password-reset-confirm/${route.params.uidb64}/${route.params.token}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        new_password: newPassword.value,
        new_password_confirm: confirmPassword.value
      })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to reset password')
    }
    
    success.value = data.message || 'Password reset successfully'
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
    
  } catch (err) {
    console.error('Password reset confirmation failed:', err)
    error.value = err instanceof Error ? err.message : 'Failed to reset password. Please try again.'
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

onMounted(() => {
  // If we have email in query params, pre-fill it
  if (route.query.email) {
    email.value = route.query.email as string
  }
})
</script>

<style scoped>
.reset-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2563EB, #10B981);
  padding: 1rem;
}

.reset-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.reset-header {
  text-align: center;
  margin-bottom: 2rem;
}

.reset-header h2 {
  color: #2563EB;
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.reset-header p {
  color: #6B7280;
  margin: 0;
  font-size: 0.875rem;
}

.reset-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.form-input {
  padding: 0.75rem;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus {
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

.reset-button {
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

.reset-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.reset-button:disabled {
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

.error-text {
  color: #DC2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.reset-footer {
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #E5E7EB;
}

.reset-footer p {
  color: #6B7280;
  font-size: 0.875rem;
  margin: 0;
}

.link {
  color: #2563EB;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}
</style> 