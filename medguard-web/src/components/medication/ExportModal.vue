<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits<{
  close: []
  export: [format: string, dataType: string]
}>()

const exportFormat = ref<'json' | 'csv' | 'pdf' | 'xml'>('json')
const dataType = ref<'medications' | 'schedule' | 'adherence' | 'all'>('medications')
const includeHistory = ref(false)
const dateRange = ref<'7d' | '30d' | '90d' | 'custom'>('30d')
const customStartDate = ref('')
const customEndDate = ref('')

const handleExport = () => {
  emit('export', exportFormat.value, dataType.value)
}

const getExportDescription = () => {
  const formatNames = {
    json: 'JSON',
    csv: 'CSV',
    pdf: 'PDF',
    xml: 'XML'
  }
  
  const dataNames = {
    medications: t('dashboard.medicationList'),
    schedule: t('dashboard.schedule'),
    adherence: t('dashboard.adherence'),
    all: t('dashboard.allData')
  }
  
  return `${formatNames[exportFormat.value]} - ${dataNames[dataType.value]}`
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-2xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('dashboard.exportData') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="space-y-6">
        <!-- Export Format -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast font-medium">{{ t('dashboard.exportFormat') }}</span>
          </label>
          <div class="grid grid-cols-2 gap-4">
            <label class="cursor-pointer">
              <input 
                type="radio" 
                name="format" 
                value="json" 
                v-model="exportFormat"
                class="peer sr-only"
              />
              <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                <div class="card-body p-4 text-center">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <div class="font-medium">JSON</div>
                  <div class="text-xs opacity-75">{{ t('dashboard.jsonDescription') }}</div>
                </div>
              </div>
            </label>
            
            <label class="cursor-pointer">
              <input 
                type="radio" 
                name="format" 
                value="csv" 
                v-model="exportFormat"
                class="peer sr-only"
              />
              <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                <div class="card-body p-4 text-center">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  <div class="font-medium">CSV</div>
                  <div class="text-xs opacity-75">{{ t('dashboard.csvDescription') }}</div>
                </div>
              </div>
            </label>
            
            <label class="cursor-pointer">
              <input 
                type="radio" 
                name="format" 
                value="pdf" 
                v-model="exportFormat"
                class="peer sr-only"
              />
              <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                <div class="card-body p-4 text-center">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <div class="font-medium">PDF</div>
                  <div class="text-xs opacity-75">{{ t('dashboard.pdfDescription') }}</div>
                </div>
              </div>
            </label>
            
            <label class="cursor-pointer">
              <input 
                type="radio" 
                name="format" 
                value="xml" 
                v-model="exportFormat"
                class="peer sr-only"
              />
              <div class="card bg-base-200 peer-checked:bg-primary peer-checked:text-primary-content cursor-pointer">
                <div class="card-body p-4 text-center">
                  <svg class="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <div class="font-medium">XML</div>
                  <div class="text-xs opacity-75">{{ t('dashboard.xmlDescription') }}</div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <!-- Data Type -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast font-medium">{{ t('dashboard.dataType') }}</span>
          </label>
          <select v-model="dataType" class="select select-bordered">
            <option value="medications">{{ t('dashboard.medicationList') }}</option>
            <option value="schedule">{{ t('dashboard.schedule') }}</option>
            <option value="adherence">{{ t('dashboard.adherence') }}</option>
            <option value="all">{{ t('dashboard.allData') }}</option>
          </select>
        </div>

        <!-- Date Range -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast font-medium">{{ t('dashboard.dateRange') }}</span>
          </label>
          <div class="grid grid-cols-2 gap-4">
            <select v-model="dateRange" class="select select-bordered">
              <option value="7d">{{ t('dashboard.last7Days') }}</option>
              <option value="30d">{{ t('dashboard.last30Days') }}</option>
              <option value="90d">{{ t('dashboard.last90Days') }}</option>
              <option value="custom">{{ t('dashboard.customRange') }}</option>
            </select>
            
            <div v-if="dateRange === 'custom'" class="grid grid-cols-2 gap-2">
              <input 
                v-model="customStartDate"
                type="date" 
                class="input input-bordered"
                :placeholder="t('dashboard.startDate')"
              />
              <input 
                v-model="customEndDate"
                type="date" 
                class="input input-bordered"
                :placeholder="t('dashboard.endDate')"
              />
            </div>
          </div>
        </div>

        <!-- Options -->
        <div class="form-control">
          <label class="label cursor-pointer">
            <span class="label-text text-high-contrast font-medium">{{ t('dashboard.includeHistory') }}</span>
            <input 
              v-model="includeHistory"
              type="checkbox" 
              class="checkbox checkbox-primary"
            />
          </label>
          <label class="label">
            <span class="label-text-alt text-secondary-high-contrast">{{ t('dashboard.includeHistoryDescription') }}</span>
          </label>
        </div>

        <!-- Export Preview -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h4 class="card-title text-high-contrast">{{ t('dashboard.exportPreview') }}</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-secondary-high-contrast">{{ t('dashboard.format') }}:</span>
                <span class="font-medium">{{ exportFormat.toUpperCase() }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-secondary-high-contrast">{{ t('dashboard.dataType') }}:</span>
                <span class="font-medium">{{ dataType === 'medications' ? t('dashboard.medicationList') : dataType === 'schedule' ? t('dashboard.schedule') : dataType === 'adherence' ? t('dashboard.adherence') : t('dashboard.allData') }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-secondary-high-contrast">{{ t('dashboard.dateRange') }}:</span>
                <span class="font-medium">{{ dateRange === '7d' ? t('dashboard.last7Days') : dateRange === '30d' ? t('dashboard.last30Days') : dateRange === '90d' ? t('dashboard.last90Days') : t('dashboard.customRange') }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-secondary-high-contrast">{{ t('dashboard.includeHistory') }}:</span>
                <span class="font-medium">{{ includeHistory ? t('common.yes') : t('common.no') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Help Information -->
        <div class="alert alert-info">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-bold">{{ t('dashboard.exportTips') }}</h3>
            <ul class="text-sm mt-2 space-y-1">
              <li>• {{ t('dashboard.tipJsonFormat') }}</li>
              <li>• {{ t('dashboard.tipCsvFormat') }}</li>
              <li>• {{ t('dashboard.tipPdfFormat') }}</li>
              <li>• {{ t('dashboard.tipDataPrivacy') }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button @click="emit('close')" class="btn">{{ t('common.cancel') }}</button>
        <button @click="handleExport" class="btn btn-primary">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('dashboard.export') }}
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