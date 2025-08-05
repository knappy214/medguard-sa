<template>
  <div class="prescription-review-demo">
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <h1 class="card-title text-3xl font-bold mb-4">
          <i class="fas fa-clipboard-check text-primary mr-3"></i>
          Prescription Review Interface Demo
        </h1>
        <p class="text-base-content/70 text-lg">
          This demo showcases the comprehensive prescription review interface with 21 medications, 
          featuring inline editing, confidence scores, validation, interactions, alternatives, 
          and digital signature approval workflow.
        </p>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">Total Medications</div>
            <div class="stat-value text-primary">21</div>
            <div class="stat-desc">Sample prescription medications</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">Features</div>
            <div class="stat-value text-success">10</div>
            <div class="stat-desc">Comprehensive review capabilities</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">Compliance</div>
            <div class="stat-value text-info">SA</div>
            <div class="stat-desc">South African regulations</div>
          </div>
        </div>
      </div>
    </div>

    <PrescriptionReviewInterface 
      :medications="sampleMedications"
      @approve="handleApproval"
      @reject="handleRejection"
      @update="handleUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { PrescriptionMedication } from '@/types/medication'
import PrescriptionReviewInterface from './PrescriptionReviewInterface.vue'

// Sample medications data
const sampleMedications = ref<PrescriptionMedication[]>([
  {
    id: 'med-1',
    name: 'Amoxicillin',
    genericName: 'Amoxicillin trihydrate',
    strength: '500mg',
    dosage: '1 capsule',
    frequency: 'Three times daily',
    quantity: 21,
    refills: 2,
    instructions: 'Take with food. Complete full course.',
    cost: 45.50,
    drugDatabaseId: 'DB01060'
  },
  {
    id: 'med-2',
    name: 'Ibuprofen',
    genericName: 'Ibuprofen',
    strength: '400mg',
    dosage: '1 tablet',
    frequency: 'Every 6 hours as needed',
    quantity: 30,
    refills: 3,
    instructions: 'Take with food. Do not exceed 6 tablets per day.',
    cost: 28.75,
    drugDatabaseId: 'DB01050'
  },
  {
    id: 'med-3',
    name: 'Omeprazole',
    genericName: 'Omeprazole magnesium',
    strength: '20mg',
    dosage: '1 capsule',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take before breakfast. Swallow whole.',
    cost: 89.90,
    drugDatabaseId: 'DB00338'
  },
  {
    id: 'med-4',
    name: 'Metformin',
    genericName: 'Metformin hydrochloride',
    strength: '500mg',
    dosage: '1 tablet',
    frequency: 'Twice daily',
    quantity: 60,
    refills: 3,
    instructions: 'Take with meals. Monitor blood sugar.',
    cost: 67.25,
    drugDatabaseId: 'DB00331'
  },
  {
    id: 'med-5',
    name: 'Lisinopril',
    genericName: 'Lisinopril',
    strength: '10mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the morning. Monitor blood pressure.',
    cost: 52.40,
    drugDatabaseId: 'DB00722'
  },
  {
    id: 'med-6',
    name: 'Atorvastatin',
    genericName: 'Atorvastatin calcium',
    strength: '20mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the evening. Avoid grapefruit.',
    cost: 78.60,
    drugDatabaseId: 'DB01076'
  },
  {
    id: 'med-7',
    name: 'Amlodipine',
    genericName: 'Amlodipine besylate',
    strength: '5mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take at the same time daily.',
    cost: 45.30,
    drugDatabaseId: 'DB00381'
  },
  {
    id: 'med-8',
    name: 'Sertraline',
    genericName: 'Sertraline hydrochloride',
    strength: '50mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the morning. May take 2-4 weeks to work.',
    cost: 95.20,
    drugDatabaseId: 'DB01104'
  },
  {
    id: 'med-9',
    name: 'Pantoprazole',
    genericName: 'Pantoprazole sodium',
    strength: '40mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take before breakfast. Swallow whole.',
    cost: 112.80,
    drugDatabaseId: 'DB00213'
  },
  {
    id: 'med-10',
    name: 'Losartan',
    genericName: 'Losartan potassium',
    strength: '50mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take at the same time daily.',
    cost: 68.45,
    drugDatabaseId: 'DB00678'
  },
  {
    id: 'med-11',
    name: 'Simvastatin',
    genericName: 'Simvastatin',
    strength: '20mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the evening. Avoid grapefruit.',
    cost: 42.90,
    drugDatabaseId: 'DB00641'
  },
  {
    id: 'med-12',
    name: 'Citalopram',
    genericName: 'Citalopram hydrobromide',
    strength: '20mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the morning. May take 2-4 weeks to work.',
    cost: 88.75,
    drugDatabaseId: 'DB00215'
  },
  {
    id: 'med-13',
    name: 'Furosemide',
    genericName: 'Furosemide',
    strength: '40mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the morning. Monitor fluid intake.',
    cost: 35.60,
    drugDatabaseId: 'DB00695'
  },
  {
    id: 'med-14',
    name: 'Tramadol',
    genericName: 'Tramadol hydrochloride',
    strength: '50mg',
    dosage: '1 tablet',
    frequency: 'Every 6 hours as needed',
    quantity: 20,
    refills: 1,
    instructions: 'Take with food. Do not exceed 4 tablets per day.',
    cost: 125.40,
    drugDatabaseId: 'DB00193'
  },
  {
    id: 'med-15',
    name: 'Diclofenac',
    genericName: 'Diclofenac sodium',
    strength: '50mg',
    dosage: '1 tablet',
    frequency: 'Three times daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take with food. Monitor for stomach upset.',
    cost: 58.90,
    drugDatabaseId: 'DB00586'
  },
  {
    id: 'med-16',
    name: 'Escitalopram',
    genericName: 'Escitalopram oxalate',
    strength: '10mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the morning. May take 2-4 weeks to work.',
    cost: 102.30,
    drugDatabaseId: 'DB01175'
  },
  {
    id: 'med-17',
    name: 'Warfarin',
    genericName: 'Warfarin sodium',
    strength: '5mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 1,
    instructions: 'Take at the same time daily. Monitor INR regularly.',
    cost: 28.50,
    drugDatabaseId: 'DB00682'
  },
  {
    id: 'med-18',
    name: 'Levothyroxine',
    genericName: 'Levothyroxine sodium',
    strength: '50mcg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take on empty stomach, 30 minutes before breakfast.',
    cost: 45.80,
    drugDatabaseId: 'DB00451'
  },
  {
    id: 'med-19',
    name: 'Albuterol',
    genericName: 'Albuterol sulfate',
    strength: '100mcg',
    dosage: '2 puffs',
    frequency: 'Every 4-6 hours as needed',
    quantity: 1,
    refills: 2,
    instructions: 'Shake well before use. Rinse mouth after use.',
    cost: 156.70,
    drugDatabaseId: 'DB00860'
  },
  {
    id: 'med-20',
    name: 'Cetirizine',
    genericName: 'Cetirizine hydrochloride',
    strength: '10mg',
    dosage: '1 tablet',
    frequency: 'Once daily',
    quantity: 30,
    refills: 2,
    instructions: 'Take in the evening. May cause drowsiness.',
    cost: 38.90,
    drugDatabaseId: 'DB00341'
  },
  {
    id: 'med-21',
    name: 'Paracetamol',
    genericName: 'Paracetamol',
    strength: '500mg',
    dosage: '2 tablets',
    frequency: 'Every 6 hours as needed',
    quantity: 40,
    refills: 3,
    instructions: 'Take with water. Do not exceed 8 tablets per day.',
    cost: 22.50,
    drugDatabaseId: 'DB00316'
  }
])

// Event handlers
const handleApproval = (medications: PrescriptionMedication[]) => {
  console.log('Prescription approved:', medications)
  alert(`Prescription approved with ${medications.length} medications!`)
}

const handleRejection = (medications: PrescriptionMedication[]) => {
  console.log('Prescription rejected:', medications)
  alert(`Prescription rejected with ${medications.length} medications.`)
}

const handleUpdate = (medications: PrescriptionMedication[]) => {
  console.log('Medications updated:', medications)
  // In a real app, this would save to the backend
}
</script>

<style scoped>
.prescription-review-demo {
  @apply space-y-6;
}

.stat {
  @apply transition-all duration-200 hover:shadow-md;
}
</style> 