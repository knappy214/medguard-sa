<template>
  <div class="container mx-auto p-4 lg:p-8">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="flex justify-center mb-4">
          <Logo size="lg" :show-text="false" />
        </div>
        <h1 class="text-3xl font-bold text-primary">Profile Settings</h1>
        <p class="text-base-content/70 mt-2">Manage your healthcare account information</p>
      </div>

      <!-- Success/Error Messages -->
      <div v-if="success" class="alert alert-success mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ success }}</span>
      </div>

      <div v-if="error" class="alert alert-error mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ error }}</span>
      </div>

      <!-- Profile Form -->
      <form @submit.prevent="handleUpdateProfile" class="space-y-8">
        <!-- Avatar Section -->
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Profile Picture
            </h2>
            
            <div class="flex flex-col items-center space-y-4">
              <!-- Current Avatar -->
              <Avatar 
                :src="avatarUrl"
                :name="fullName"
                :email="profileData.email"
                size="2xl"
                alt="Profile picture"
              />
              
              <!-- Avatar Upload -->
              <div class="flex flex-col sm:flex-row gap-2">
                <input
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  @change="handleAvatarChange"
                  class="file-input file-input-bordered file-input-primary w-full max-w-xs"
                />
                <button 
                  type="button" 
                  @click="() => avatarInput?.click()"
                  class="btn btn-primary"
                  :disabled="avatarUploading"
                >
                  <span v-if="avatarUploading" class="loading loading-spinner loading-sm"></span>
                  {{ avatarUploading ? 'Uploading...' : 'Choose Image' }}
                </button>
                <button 
                  v-if="avatarUrl"
                  type="button" 
                  @click="removeAvatar"
                  class="btn btn-outline btn-error"
                  :disabled="avatarUploading"
                >
                  Remove
                </button>
              </div>
              
              <p class="text-sm text-base-content/70">
                Supported formats: JPG, PNG, GIF, WebP (max 5MB, 2048x2048px)
              </p>
            </div>
          </div>
        </div>

        <!-- Personal Information -->
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Personal Information
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="firstName" class="label">
                  <span class="label-text font-medium">First Name</span>
                </label>
                <input
                  id="firstName"
                  v-model="profileData.first_name"
                  type="text"
                  required
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
                  v-model="profileData.last_name"
                  type="text"
                  required
                  placeholder="Enter your last name"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="email" class="label">
                  <span class="label-text font-medium">Email Address</span>
                </label>
                <input
                  id="email"
                  v-model="profileData.email"
                  type="email"
                  required
                  placeholder="Enter your email address"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
              
              <div class="form-control">
                <label for="phone" class="label">
                  <span class="label-text font-medium">Phone Number</span>
                </label>
                <input
                  id="phone"
                  v-model="profileData.phone"
                  type="tel"
                  placeholder="Enter your phone number"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="dateOfBirth" class="label">
                  <span class="label-text font-medium">Date of Birth</span>
                </label>
                <input
                  id="dateOfBirth"
                  v-model="profileData.date_of_birth"
                  type="date"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
              
              <div class="form-control">
                <label for="gender" class="label">
                  <span class="label-text font-medium">Gender</span>
                </label>
                <select v-model="profileData.gender" class="select select-bordered w-full focus:select-primary">
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
            </div>

            <div class="form-control">
              <label for="address" class="label">
                <span class="label-text font-medium">Address</span>
              </label>
              <textarea
                id="address"
                v-model="profileData.address"
                placeholder="Enter your full address"
                class="textarea textarea-bordered w-full focus:textarea-primary"
                rows="3"
              ></textarea>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="form-control">
                <label for="city" class="label">
                  <span class="label-text font-medium">City</span>
                </label>
                <input
                  id="city"
                  v-model="profileData.city"
                  type="text"
                  placeholder="Enter your city"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
              
              <div class="form-control">
                <label for="province" class="label">
                  <span class="label-text font-medium">Province</span>
                </label>
                <select v-model="profileData.province" class="select select-bordered w-full focus:select-primary">
                  <option value="">Select province</option>
                  <option value="gauteng">Gauteng</option>
                  <option value="western_cape">Western Cape</option>
                  <option value="kwazulu_natal">KwaZulu-Natal</option>
                  <option value="eastern_cape">Eastern Cape</option>
                  <option value="free_state">Free State</option>
                  <option value="mpumalanga">Mpumalanga</option>
                  <option value="limpopo">Limpopo</option>
                  <option value="north_west">North West</option>
                  <option value="northern_cape">Northern Cape</option>
                </select>
              </div>
              
              <div class="form-control">
                <label for="postalCode" class="label">
                  <span class="label-text font-medium">Postal Code</span>
                </label>
                <input
                  id="postalCode"
                  v-model="profileData.postal_code"
                  type="text"
                  placeholder="Enter postal code"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Medical Information -->
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              Medical Information
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="bloodType" class="label">
                  <span class="label-text font-medium">Blood Type</span>
                </label>
                <select v-model="profileData.blood_type" class="select select-bordered w-full focus:select-primary">
                  <option value="">Select blood type</option>
                  <option value="a_positive">A+</option>
                  <option value="a_negative">A-</option>
                  <option value="b_positive">B+</option>
                  <option value="b_negative">B-</option>
                  <option value="ab_positive">AB+</option>
                  <option value="ab_negative">AB-</option>
                  <option value="o_positive">O+</option>
                  <option value="o_negative">O-</option>
                </select>
              </div>
              
              <div class="form-control">
                <label for="allergies" class="label">
                  <span class="label-text font-medium">Allergies</span>
                </label>
                <input
                  id="allergies"
                  v-model="profileData.allergies"
                  type="text"
                  placeholder="Enter allergies (comma separated)"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>

            <div class="form-control">
              <label for="medicalConditions" class="label">
                <span class="label-text font-medium">Medical Conditions</span>
              </label>
              <textarea
                id="medicalConditions"
                v-model="profileData.medical_conditions"
                placeholder="Enter any medical conditions or chronic illnesses"
                class="textarea textarea-bordered w-full focus:textarea-primary"
                rows="3"
              ></textarea>
            </div>

            <div class="form-control">
              <label for="currentMedications" class="label">
                <span class="label-text font-medium">Current Medications</span>
              </label>
              <textarea
                id="currentMedications"
                v-model="profileData.current_medications"
                placeholder="List current medications and dosages"
                class="textarea textarea-bordered w-full focus:textarea-primary"
                rows="3"
              ></textarea>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="emergencyContact" class="label">
                  <span class="label-text font-medium">Emergency Contact Name</span>
                </label>
                <input
                  id="emergencyContact"
                  v-model="profileData.emergency_contact_name"
                  type="text"
                  placeholder="Enter emergency contact name"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
              
              <div class="form-control">
                <label for="emergencyPhone" class="label">
                  <span class="label-text font-medium">Emergency Contact Phone</span>
                </label>
                <input
                  id="emergencyPhone"
                  v-model="profileData.emergency_contact_phone"
                  type="tel"
                  placeholder="Enter emergency contact phone"
                  class="input input-bordered w-full focus:input-primary"
                />
              </div>
            </div>

            <div class="form-control">
              <label for="emergencyRelationship" class="label">
                <span class="label-text font-medium">Relationship to Emergency Contact</span>
              </label>
              <select v-model="profileData.emergency_contact_relationship" class="select select-bordered w-full focus:select-primary">
                <option value="">Select relationship</option>
                <option value="spouse">Spouse</option>
                <option value="parent">Parent</option>
                <option value="child">Child</option>
                <option value="sibling">Sibling</option>
                <option value="friend">Friend</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Account Settings -->
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body">
            <h2 class="card-title text-xl mb-4">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Account Settings
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-control">
                <label for="language" class="label">
                  <span class="label-text font-medium">Preferred Language</span>
                </label>
                <select v-model="profileData.preferred_language" class="select select-bordered w-full focus:select-primary">
                  <option value="en">English</option>
                  <option value="af">Afrikaans</option>
                </select>
              </div>
              
              <div class="form-control">
                <label for="timezone" class="label">
                  <span class="label-text font-medium">Timezone</span>
                </label>
                <select v-model="profileData.timezone" class="select select-bordered w-full focus:select-primary">
                  <option value="Africa/Johannesburg">South Africa Standard Time (SAST)</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text font-medium">Email Notifications</span>
                <input
                  v-model="profileData.email_notifications"
                  type="checkbox"
                  class="toggle toggle-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text font-medium">SMS Notifications</span>
                <input
                  v-model="profileData.sms_notifications"
                  type="checkbox"
                  class="toggle toggle-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text font-medium">Two-Factor Authentication</span>
                <input
                  v-model="profileData.mfa_enabled"
                  type="checkbox"
                  class="toggle toggle-primary"
                />
              </label>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="flex justify-end gap-4">
          <button type="button" @click="resetForm" class="btn btn-outline">
            Reset
          </button>
          <button type="submit" :disabled="loading" class="btn btn-primary">
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            {{ loading ? 'Updating...' : 'Update Profile' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import authService from '@/services/authService'
import { useAuth } from '@/composables/useAuth'
import Logo from '@/components/common/Logo.vue'
import Avatar from '@/components/common/Avatar.vue'

const { refreshUserProfile } = useAuth()

const loading = ref(false)
const avatarUploading = ref(false)
const error = ref('')
const success = ref('')
const avatarUrl = ref('')
const avatarInput = ref<HTMLInputElement>()

const profileData = reactive({
  // Personal Information
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  date_of_birth: '',
  gender: '',
  address: '',
  city: '',
  province: '',
  postal_code: '',
  
  // Medical Information
  blood_type: '',
  allergies: '',
  medical_conditions: '',
  current_medications: '',
  emergency_contact_name: '',
  emergency_contact_phone: '',
  emergency_contact_relationship: '',
  
  // Account Settings
  preferred_language: 'en',
  timezone: 'Africa/Johannesburg',
  email_notifications: true,
  sms_notifications: false,
  mfa_enabled: false
})

const originalData = ref({})

// Computed property for full name that handles empty values
const fullName = computed(() => {
  const firstName = profileData.first_name?.trim() || ''
  const lastName = profileData.last_name?.trim() || ''
  return `${firstName} ${lastName}`.trim() || ''
})

const loadProfile = async () => {
  try {
    const response = await fetch('/api/users/profile/me/', {
      headers: {
        'Authorization': `Bearer ${await authService.getAccessToken()}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      Object.assign(profileData, data)
      originalData.value = { ...data }
      
      // Set avatar URL
      if (data.avatar_url) {
        avatarUrl.value = data.avatar_url
      }
    } else {
      throw new Error('Failed to load profile data')
    }
  } catch (err) {
    console.error('Failed to load profile:', err)
    error.value = 'Failed to load profile data'
  }
}

const handleUpdateProfile = async () => {
  try {
    loading.value = true
    error.value = ''
    success.value = ''
    
    const response = await fetch('/api/users/profile/me/', {
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
    originalData.value = { ...profileData }
    
    // Refresh user profile in auth service to update avatar in navigation
    await refreshUserProfile()
    
  } catch (err) {
    console.error('Profile update failed:', err)
    error.value = err instanceof Error ? err.message : 'Failed to update profile'
  } finally {
    loading.value = false
  }
}

const handleAvatarChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  try {
    avatarUploading.value = true
    error.value = ''
    
    const formData = new FormData()
    formData.append('image', file)
    
    const response = await fetch('/api/users/profile/avatar/upload/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${await authService.getAccessToken()}`
      },
      body: formData
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to upload avatar')
    }
    
    avatarUrl.value = data.url
    success.value = 'Avatar uploaded successfully'
    
    // Refresh user profile in auth service to update avatar in navigation
    await refreshUserProfile()
    
  } catch (err) {
    console.error('Avatar upload failed:', err)
    error.value = err instanceof Error ? err.message : 'Failed to upload avatar'
  } finally {
    avatarUploading.value = false
    // Reset file input
    if (target) target.value = ''
  }
}

const removeAvatar = async () => {
  try {
    const response = await fetch('/api/users/profile/avatar/delete/', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${await authService.getAccessToken()}`
      }
    })
    
    if (response.ok) {
      avatarUrl.value = ''
      success.value = 'Avatar removed successfully'
      
      // Refresh user profile in auth service to update avatar in navigation
      await refreshUserProfile()
    } else {
      throw new Error('Failed to remove avatar')
    }
  } catch (err) {
    console.error('Avatar removal failed:', err)
    error.value = 'Failed to remove avatar'
  }
}

const resetForm = () => {
  Object.assign(profileData, originalData.value)
  error.value = ''
  success.value = ''
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