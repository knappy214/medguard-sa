/**
 * Schedule Generator Usage Examples
 * 
 * This file demonstrates how to use the comprehensive schedule generator
 * for various medication scenarios including complex cases like insulin,
 * multiple daily doses, and medication interactions.
 */

import { scheduleGenerator, type LifestylePreferences, type OptimizedSchedule, type MedicationCalendar } from './scheduleGenerator'
import type { Medication } from '@/types/medication'

/**
 * Example 1: Basic medication schedule generation
 */
export async function exampleBasicSchedule() {
  console.log('📋 Example 1: Basic Medication Schedule')
  
  // Sample medications
  const medications: Medication[] = [
    {
      id: '1',
      name: 'Metformin',
      dosage: '500mg',
      frequency: 'Twice daily',
      time: '08:00',
      stock: 60,
      pill_count: 60,
      minStock: 10,
      instructions: 'Take with food to reduce stomach upset',
      category: 'Diabetes',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: '2',
      name: 'Lisinopril',
      dosage: '10mg',
      frequency: 'Once daily',
      time: '08:00',
      stock: 30,
      pill_count: 30,
      minStock: 5,
      instructions: 'Take in the morning, may cause dizziness',
      category: 'Blood Pressure',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  // Patient lifestyle preferences
  const lifestylePreferences: LifestylePreferences = {
    wakeUpTime: '07:00',
    bedTime: '22:00',
    mealTimes: {
      breakfast: '08:00',
      lunch: '12:30',
      dinner: '18:30'
    },
    workSchedule: {
      startTime: '09:00',
      endTime: '17:00',
      daysOfWeek: [1, 2, 3, 4, 5] // Monday to Friday
    },
    preferredReminderTimes: ['07:30', '12:00', '18:00'],
    avoidTimes: ['14:00', '15:00'], // Avoid afternoon slump
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['08:00', '12:30', '18:30'],
      worstTimes: ['14:00', '15:00', '21:00'],
      missedDosePatterns: ['forgot morning dose', 'late evening dose']
    }
  }

  try {
    const optimizedSchedules = await scheduleGenerator.generateOptimalSchedules(
      medications,
      lifestylePreferences
    )

    console.log('✅ Generated schedules:', optimizedSchedules)
    
    // Generate calendar view
    const calendar = scheduleGenerator.generateMedicationCalendar(optimizedSchedules)
    console.log('📅 Calendar view:', calendar)
    
    return { schedules: optimizedSchedules, calendar }
  } catch (error) {
    console.error('❌ Failed to generate schedules:', error)
    throw error
  }
}

/**
 * Example 2: Complex insulin schedule with variable dosing
 */
export async function exampleInsulinSchedule() {
  console.log('💉 Example 2: Insulin Schedule with Variable Dosing')
  
  const insulinMedications: Medication[] = [
    {
      id: 'insulin-1',
      name: 'NovoRapid Insulin',
      dosage: 'Variable',
      frequency: 'Three times daily',
      time: '08:00',
      stock: 100,
      pill_count: 100,
      minStock: 20,
      instructions: 'Adjust dose based on blood glucose and carbohydrate intake. Take before meals.',
      category: 'Diabetes - Insulin',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'insulin-2',
      name: 'Lantus Insulin',
      dosage: 'Variable',
      frequency: 'Once daily',
      time: '22:00',
      stock: 100,
      pill_count: 100,
      minStock: 20,
      instructions: 'Long-acting insulin. Take at bedtime. Adjust based on morning blood glucose.',
      category: 'Diabetes - Insulin',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  const diabeticLifestyle: LifestylePreferences = {
    wakeUpTime: '06:30',
    bedTime: '22:30',
    mealTimes: {
      breakfast: '07:30',
      lunch: '12:00',
      dinner: '18:00'
    },
    workSchedule: {
      startTime: '08:00',
      endTime: '16:00',
      daysOfWeek: [1, 2, 3, 4, 5]
    },
    preferredReminderTimes: ['07:00', '11:30', '17:30', '21:30'],
    avoidTimes: [],
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['07:30', '12:00', '18:00', '22:00'],
      worstTimes: ['14:00'],
      missedDosePatterns: ['forgot to check blood glucose', 'late meal timing']
    }
  }

  try {
    const insulinSchedules = await scheduleGenerator.generateOptimalSchedules(
      insulinMedications,
      diabeticLifestyle
    )

    console.log('✅ Insulin schedules:', insulinSchedules)
    
    // Check for variable dosing features
    insulinSchedules.forEach(schedule => {
      schedule.schedules.forEach(dose => {
        if (dose.variableDosing) {
          console.log(`💉 Variable dosing for ${schedule.medication.name}:`, dose.variableDosing)
        }
      })
    })
    
    return insulinSchedules
  } catch (error) {
    console.error('❌ Failed to generate insulin schedules:', error)
    throw error
  }
}

/**
 * Example 3: Multiple medications with potential interactions
 */
export async function exampleComplexMedicationSchedule() {
  console.log('💊 Example 3: Complex Medication Schedule with Interactions')
  
  const complexMedications: Medication[] = [
    {
      id: 'med-1',
      name: 'Warfarin',
      dosage: '5mg',
      frequency: 'Once daily',
      time: '18:00',
      stock: 30,
      pill_count: 30,
      minStock: 5,
      instructions: 'Take at the same time daily. Avoid alcohol. Monitor INR regularly.',
      category: 'Blood Thinner',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'med-2',
      name: 'Aspirin',
      dosage: '81mg',
      frequency: 'Once daily',
      time: '08:00',
      stock: 90,
      pill_count: 90,
      minStock: 10,
      instructions: 'Take with food to prevent stomach upset.',
      category: 'Blood Thinner',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'med-3',
      name: 'Omeprazole',
      dosage: '20mg',
      frequency: 'Once daily',
      time: '08:00',
      stock: 30,
      pill_count: 30,
      minStock: 5,
      instructions: 'Take on empty stomach 30 minutes before breakfast.',
      category: 'Stomach Acid',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'med-4',
      name: 'Ibuprofen',
      dosage: '400mg',
      frequency: 'As needed',
      time: '09:00',
      stock: 50,
      pill_count: 50,
      minStock: 10,
      instructions: 'Take as needed for pain. Avoid if taking other blood thinners.',
      category: 'Pain Relief',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  const elderlyLifestyle: LifestylePreferences = {
    wakeUpTime: '08:00',
    bedTime: '21:00',
    mealTimes: {
      breakfast: '08:30',
      lunch: '13:00',
      dinner: '18:00'
    },
    workSchedule: undefined, // Retired
    preferredReminderTimes: ['08:00', '12:30', '17:30'],
    avoidTimes: ['22:00', '23:00'], // Avoid late night medications
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['08:30', '13:00', '18:00'],
      worstTimes: ['21:00', '22:00'],
      missedDosePatterns: ['forgot evening dose', 'confused about timing']
    }
  }

  try {
    const complexSchedules = await scheduleGenerator.generateOptimalSchedules(
      complexMedications,
      elderlyLifestyle
    )

    console.log('✅ Complex medication schedules:', complexSchedules)
    
    // Check for conflicts and interactions
    complexSchedules.forEach(schedule => {
      if (schedule.conflicts.length > 0) {
        console.log(`⚠️ Conflicts for ${schedule.medication.name}:`, schedule.conflicts)
      }
      if (schedule.optimizationNotes.length > 0) {
        console.log(`📝 Optimization notes for ${schedule.medication.name}:`, schedule.optimizationNotes)
      }
    })
    
    return complexSchedules
  } catch (error) {
    console.error('❌ Failed to generate complex schedules:', error)
    throw error
  }
}

/**
 * Example 4: "As needed" medications with tracking
 */
export async function exampleAsNeededMedications() {
  console.log('🔄 Example 4: As Needed Medications with Tracking')
  
  const asNeededMedications: Medication[] = [
    {
      id: 'prn-1',
      name: 'Albuterol Inhaler',
      dosage: '2 puffs',
      frequency: 'As needed',
      time: '09:00',
      stock: 1,
      pill_count: 1,
      minStock: 1,
      instructions: 'Use as needed for shortness of breath. Maximum 8 puffs per day.',
      category: 'Asthma',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'prn-2',
      name: 'Acetaminophen',
      dosage: '500mg',
      frequency: 'As needed',
      time: '09:00',
      stock: 100,
      pill_count: 100,
      minStock: 20,
      instructions: 'Take as needed for pain or fever. Maximum 4g per day.',
      category: 'Pain Relief',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  const activeLifestyle: LifestylePreferences = {
    wakeUpTime: '06:00',
    bedTime: '23:00',
    mealTimes: {
      breakfast: '07:00',
      lunch: '12:00',
      dinner: '19:00'
    },
    workSchedule: {
      startTime: '08:00',
      endTime: '17:00',
      daysOfWeek: [1, 2, 3, 4, 5]
    },
    preferredReminderTimes: ['07:00', '12:00', '19:00'],
    avoidTimes: [],
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['07:00', '12:00', '19:00'],
      worstTimes: ['14:00'],
      missedDosePatterns: ['forgot to carry inhaler', 'busy at work']
    }
  }

  try {
    const prnSchedules = await scheduleGenerator.generateOptimalSchedules(
      asNeededMedications,
      activeLifestyle
    )

    console.log('✅ As needed medication schedules:', prnSchedules)
    
    // Check for as-needed features
    prnSchedules.forEach(schedule => {
      schedule.schedules.forEach(dose => {
        if (dose.isAsNeeded) {
          console.log(`🔄 As needed medication: ${schedule.medication.name}`, {
            reminderSettings: dose.reminderSettings,
            instructions: dose.instructions
          })
        }
      })
    })
    
    return prnSchedules
  } catch (error) {
    console.error('❌ Failed to generate as-needed schedules:', error)
    throw error
  }
}

/**
 * Example 5: Generate comprehensive medication calendar
 */
export async function exampleMedicationCalendar() {
  console.log('📅 Example 5: Comprehensive Medication Calendar')
  
  // Combine all medication types for a comprehensive calendar
  const allMedications: Medication[] = [
    // Regular medications
    {
      id: '1',
      name: 'Metformin',
      dosage: '500mg',
      frequency: 'Twice daily',
      time: '08:00',
      stock: 60,
      pill_count: 60,
      minStock: 10,
      instructions: 'Take with food',
      category: 'Diabetes',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    // Insulin
    {
      id: '2',
      name: 'NovoRapid Insulin',
      dosage: 'Variable',
      frequency: 'Three times daily',
      time: '08:00',
      stock: 100,
      pill_count: 100,
      minStock: 20,
      instructions: 'Adjust dose based on blood glucose',
      category: 'Diabetes - Insulin',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    // As needed
    {
      id: '3',
      name: 'Albuterol Inhaler',
      dosage: '2 puffs',
      frequency: 'As needed',
      time: '09:00',
      stock: 1,
      pill_count: 1,
      minStock: 1,
      instructions: 'Use as needed for shortness of breath',
      category: 'Asthma',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  const lifestyle: LifestylePreferences = {
    wakeUpTime: '07:00',
    bedTime: '22:00',
    mealTimes: {
      breakfast: '08:00',
      lunch: '12:30',
      dinner: '18:30'
    },
    workSchedule: {
      startTime: '09:00',
      endTime: '17:00',
      daysOfWeek: [1, 2, 3, 4, 5]
    },
    preferredReminderTimes: ['07:30', '12:00', '18:00'],
    avoidTimes: ['14:00'],
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['08:00', '12:30', '18:30'],
      worstTimes: ['14:00'],
      missedDosePatterns: ['forgot morning dose']
    }
  }

  try {
    // Generate optimized schedules
    const schedules = await scheduleGenerator.generateOptimalSchedules(
      allMedications,
      lifestyle
    )

    // Generate 7-day calendar
    const calendar = scheduleGenerator.generateMedicationCalendar(schedules, new Date(), 7)
    
    console.log('📅 7-day medication calendar:', calendar)
    
    // Print daily summaries
    calendar.days.forEach((day, index) => {
      const date = new Date(day.date).toLocaleDateString()
      console.log(`📆 ${date}: ${day.summary.totalDoses} total doses, ${day.summary.criticalDoses} critical`)
      
      // Show time slots with medications
      day.timeSlots.forEach(slot => {
        if (slot.medications.length > 0) {
          console.log(`  ${slot.time}: ${slot.medications.map(med => 
            `${med.medication.name} (${med.dosage}${med.unit})`
          ).join(', ')}`)
        }
      })
    })
    
    return { schedules, calendar }
  } catch (error) {
    console.error('❌ Failed to generate calendar:', error)
    throw error
  }
}

/**
 * Example 6: Schedule optimization for adherence improvement
 */
export async function exampleAdherenceOptimization() {
  console.log('📈 Example 6: Adherence Optimization')
  
  const medications: Medication[] = [
    {
      id: '1',
      name: 'Amlodipine',
      dosage: '5mg',
      frequency: 'Once daily',
      time: '08:00',
      stock: 30,
      pill_count: 30,
      minStock: 5,
      instructions: 'Take at the same time daily for best results',
      category: 'Blood Pressure',
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ]

  // Patient with poor adherence history
  const poorAdherenceLifestyle: LifestylePreferences = {
    wakeUpTime: '08:30',
    bedTime: '23:30',
    mealTimes: {
      breakfast: '09:00',
      lunch: '13:00',
      dinner: '19:00'
    },
    workSchedule: {
      startTime: '09:30',
      endTime: '18:00',
      daysOfWeek: [1, 2, 3, 4, 5]
    },
    preferredReminderTimes: ['08:00', '12:00', '18:00'],
    avoidTimes: ['07:00', '21:00'], // Patient struggles with early morning and late evening
    timezone: 'Africa/Johannesburg',
    adherenceHistory: {
      bestTimes: ['09:00', '13:00', '19:00'], // Aligns with meal times
      worstTimes: ['07:00', '08:00', '21:00', '22:00'], // Poor adherence times
      missedDosePatterns: ['forgot morning dose', 'too busy in evening', 'weekend forgetfulness']
    }
  }

  try {
    const optimizedSchedules = await scheduleGenerator.generateOptimalSchedules(
      medications,
      poorAdherenceLifestyle
    )

    console.log('✅ Adherence-optimized schedules:', optimizedSchedules)
    
    // Analyze adherence scores
    optimizedSchedules.forEach(schedule => {
      console.log(`📊 ${schedule.medication.name} adherence score: ${schedule.adherenceScore}%`)
      
      if (schedule.adherenceScore < 80) {
        console.log(`⚠️ Low adherence risk for ${schedule.medication.name}`)
        console.log(`💡 Optimization notes:`, schedule.optimizationNotes)
      }
    })
    
    return optimizedSchedules
  } catch (error) {
    console.error('❌ Failed to optimize for adherence:', error)
    throw error
  }
}

/**
 * Run all examples
 */
export async function runAllExamples() {
  console.log('🚀 Running all schedule generator examples...\n')
  
  try {
    console.log('='.repeat(50))
    await exampleBasicSchedule()
    
    console.log('\n' + '='.repeat(50))
    await exampleInsulinSchedule()
    
    console.log('\n' + '='.repeat(50))
    await exampleComplexMedicationSchedule()
    
    console.log('\n' + '='.repeat(50))
    await exampleAsNeededMedications()
    
    console.log('\n' + '='.repeat(50))
    await exampleMedicationCalendar()
    
    console.log('\n' + '='.repeat(50))
    await exampleAdherenceOptimization()
    
    console.log('\n✅ All examples completed successfully!')
  } catch (error) {
    console.error('❌ Error running examples:', error)
  }
}

// Export for use in other files
export {
  exampleBasicSchedule,
  exampleInsulinSchedule,
  exampleComplexMedicationSchedule,
  exampleAsNeededMedications,
  exampleMedicationCalendar,
  exampleAdherenceOptimization
} 