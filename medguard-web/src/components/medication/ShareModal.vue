<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication } from '@/types/medication'

const { t } = useI18n()

interface Props {
  medications: Medication[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  share: [providerData: any]
}>()

const providerType = ref<'doctor' | 'pharmacist' | 'specialist' | 'other'>('doctor')
const providerName = ref('')
const providerEmail = ref('')
const providerPhone = ref('')
const shareType = ref<'summary' | 'detailed' | 'emergency'>('summary')
const includeSchedule = ref(true)
const includeAdherence = ref(true)
const includeInteractions = ref(true)
const message = ref('')
const selectedMedications = ref<string[]>([])

const providerTypes = [
  { value: 'doctor', label: t('dashboard.doctor'), icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { value: 'pharmacist', label: t('dashboard.pharmacist'), icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  { value: 'specialist', label: t('dashboard.specialist'), icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
  { value: 'other', label: t('dashboard.other'), icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' }
]

const shareTypes = [
  { value: 'summary', label: t('dashboard.summary'), description: t('dashboard.summaryDescription') },
  { value: 'detailed', label: t('dashboard.detailed'), description: t('dashboard.detailedDescription') },
  { value: 'emergency', label: t('dashboard.emergency'), description: t('dashboard.emergencyDescription') }
]

const isFormValid = computed(() => {
  return providerName.value.trim() && 
         (providerEmail.value.trim() || providerPhone.value.trim()) &&
         selectedMedications.value.length > 0
})

const handleSelectAll = () => {
  if (selectedMedications.value.length === props.medications.length) {
    selectedMedications.value = []
  } else {
    selectedMedications.value = props.medications.map(med => med.id)
  }
}

const handleShare = () => {
  const providerData = {
    type: providerType.value,
    name: providerName.value,
    email: providerEmail.value,
    phone: providerPhone.value,
    shareType: shareType.value,
    includeSchedule: includeSchedule.value,
    includeAdherence: includeAdherence.value,
    includeInteractions: includeInteractions.value,
    message: message.value,
    medicationIds: selectedMedications.value
  }
  
  emit('share', providerData)
}

const getDefaultMessage = () => {
  const typeLabels = {
    doctor: t('dashboard.doctor'),
    pharmacist: t('dashboard.pharmacist'),
    specialist: t('dashboard.specialist'),
    other: t('dashboard.healthcareProvider')
  }
  
  return t('dashboard.defaultShareMessage', { 
    providerType: typeLabels[providerType.value],
    medicationCount: selectedMedications.value.length 
  })
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-4xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          {{ t('dashboard.shareWithProvider') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Provider Information -->
        <div class="space-y-6">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.providerInformation') }}</h4>
          
          <!-- Provider Type -->
          <div class="form-control">
            <label class="label">
              <span class="label-text text-high-contrast font-medium">{{ t('dashboard.providerType') }}</span>
            </label>
            <div class="grid grid-cols-2 gap-4">
              <label 
                v-for="type in providerTypes" 
                :key="type.value"
                class="cursor-pointer"
              >
                <input 
                  type="radio" 
                  name="providerType" 
                  :value="type.value" 
                  v-model="providerType"
                  class="peer sr-only"
                />
                <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                  <div class="card-body p-4 text-center">
                    <svg class="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="type.icon" />
                    </svg>
                    <div class="font-medium text-sm">{{ type.label }}</div>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Provider Details -->
          <div class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text text-high-contrast font-medium">{{ t('dashboard.providerName') }}</span>
              </label>
              <input 
                v-model="providerName"
                type="text" 
                class="input input-bordered"
                :placeholder="t('dashboard.enterProviderName')"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text text-high-contrast font-medium">{{ t('dashboard.providerEmail') }}</span>
              </label>
              <input 
                v-model="providerEmail"
                type="email" 
                class="input input-bordered"
                :placeholder="t('dashboard.enterProviderEmail')"
              />
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text text-high-contrast font-medium">{{ t('dashboard.providerPhone') }}</span>
              </label>
              <input 
                v-model="providerPhone"
                type="tel" 
                class="input input-bordered"
                :placeholder="t('dashboard.enterProviderPhone')"
              />
            </div>
          </div>

          <!-- Share Type -->
          <div class="form-control">
            <label class="label">
              <span class="label-text text-high-contrast font-medium">{{ t('dashboard.shareType') }}</span>
            </label>
            <div class="space-y-2">
              <label 
                v-for="type in shareTypes" 
                :key="type.value"
                class="cursor-pointer"
              >
                <input 
                  type="radio" 
                  name="shareType" 
                  :value="type.value" 
                  v-model="shareType"
                  class="peer sr-only"
                />
                <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                  <div class="card-body p-3">
                    <div class="font-medium">{{ type.label }}</div>
                    <div class="text-xs opacity-75">{{ type.description }}</div>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- Share Options -->
          <div class="space-y-3">
            <h5 class="font-medium text-high-contrast">{{ t('dashboard.shareOptions') }}</h5>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text text-high-contrast">{{ t('dashboard.includeSchedule') }}</span>
                <input 
                  v-model="includeSchedule"
                  type="checkbox" 
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text text-high-contrast">{{ t('dashboard.includeAdherence') }}</span>
                <input 
                  v-model="includeAdherence"
                  type="checkbox" 
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text text-high-contrast">{{ t('dashboard.includeInteractions') }}</span>
                <input 
                  v-model="includeInteractions"
                  type="checkbox" 
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
          </div>
        </div>

        <!-- Medication Selection -->
        <div class="space-y-6">
          <div class="flex justify-between items-center">
            <h4 class="font-semibold text-high-contrast">{{ t('dashboard.selectMedications') }}</h4>
            <button @click="handleSelectAll" class="btn btn-sm btn-outline">
              {{ selectedMedications.length === medications.length ? t('dashboard.deselectAll') : t('dashboard.selectAll') }}
            </button>
          </div>
          
          <div class="space-y-2 max-h-64 overflow-y-auto">
            <label 
              v-for="medication in medications" 
              :key="medication.id"
              class="cursor-pointer"
            >
              <input 
                type="checkbox" 
                :value="medication.id"
                v-model="selectedMedications"
                class="checkbox checkbox-primary mr-3"
              />
              <div class="inline-block">
                <div class="font-medium text-high-contrast">{{ medication.name }}</div>
                <div class="text-sm text-secondary-high-contrast">{{ medication.dosage }}</div>
              </div>
            </label>
          </div>

          <!-- Message -->
          <div class="form-control">
            <label class="label">
              <span class="label-text text-high-contrast font-medium">{{ t('dashboard.message') }}</span>
            </label>
            <textarea 
              v-model="message"
              class="textarea textarea-bordered h-24"
              :placeholder="getDefaultMessage()"
            ></textarea>
          </div>

          <!-- Share Preview -->
          <div class="card bg-base-200">
            <div class="card-body">
              <h5 class="card-title text-high-contrast">{{ t('dashboard.sharePreview') }}</h5>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-secondary-high-contrast">{{ t('dashboard.provider') }}:</span>
                  <span class="font-medium">{{ providerName || t('dashboard.notSpecified') }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-secondary-high-contrast">{{ t('dashboard.medications') }}:</span>
                  <span class="font-medium">{{ selectedMedications.length }} {{ t('dashboard.selected') }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-secondary-high-contrast">{{ t('dashboard.shareType') }}:</span>
                  <span class="font-medium">{{ shareType === 'summary' ? t('dashboard.summary') : shareType === 'detailed' ? t('dashboard.detailed') : t('dashboard.emergency') }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-secondary-high-contrast">{{ t('dashboard.contact') }}:</span>
                  <span class="font-medium">{{ providerEmail || providerPhone || t('dashboard.notSpecified') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Privacy Notice -->
      <div class="alert alert-warning mt-6">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <h3 class="font-bold">{{ t('dashboard.privacyNotice') }}</h3>
          <div class="text-sm">{{ t('dashboard.privacyNoticeDescription') }}</div>
        </div>
      </div>

      <div class="modal-action">
        <button @click="emit('close')" class="btn">{{ t('common.cancel') }}</button>
        <button 
          @click="handleShare" 
          class="btn btn-primary"
          :disabled="!isFormValid"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          {{ t('dashboard.share') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-box {
  max-height: 90vh;
  overflow-y: auto;
}
</style> 