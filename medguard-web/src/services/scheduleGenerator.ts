import type { 
  Medication, 
  MedicationSchedule, 
  MedicationFormData,
  MedicationInteraction,
  AdherenceTracking,
  MedicationHistory
} from '@/types/medication'
import { medicationApi } from './medicationApi'

/**
 * Optimal time periods for medication dosing
 */
export interface OptimalTimePeriod {
  startTime: string // HH:MM format
  endTime: string // HH:MM format
  label: string
  priority: number // 1 = highest priority
  mealRelation: 'before_meal' | 'with_meal' | 'after_meal' | 'empty_stomach' | 'any'
  description: string
}

/**
 * Medication dosing requirements
 */
export interface DosingRequirements {
  medicationId: string
  medication: Medication
  frequency: string
  totalDosesPerDay: number
  mealRequirements: 'before_meal' | 'with_meal' | 'after_meal' | 'empty_stomach' | 'any'
  minIntervalHours: number
  maxIntervalHours: number
  preferredTimes: string[] // HH:MM format
  avoidTimes: string[] // HH:MM format
  specialInstructions: string[]
  isAsNeeded: boolean
  variableDosing?: {
    minDose: number
    maxDose: number
    unit: string
    adjustmentFactors: string[]
  }
}

/**
 * Generated schedule with optimization details
 */
export interface OptimizedSchedule {
  medicationId: string
  medication: Medication
  schedules: GeneratedSchedule[]
  conflicts: ScheduleConflict[]
  adherenceScore: number
  optimizationNotes: string[]
  alternativeSchedules: GeneratedSchedule[][]
}

/**
 * Individual schedule entry
 */
export interface GeneratedSchedule {
  id: string
  time: string // HH:MM format
  dosage: number
  unit: string
  mealRelation: 'before_meal' | 'with_meal' | 'after_meal' | 'empty_stomach' | 'any'
  instructions: string
  priority: 'high' | 'medium' | 'low'
  reminderSettings: ReminderSettings
  isAsNeeded: boolean
  variableDosing?: {
    currentDose: number
    adjustmentReason?: string
  }
}

/**
 * Schedule conflict detection
 */
export interface ScheduleConflict {
  type: 'timing_overlap' | 'interaction' | 'meal_conflict' | 'dose_spacing' | 'adherence_risk'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  affectedMedications: string[]
  recommendations: string[]
  alternativeTiming?: string[]
}

/**
 * Reminder settings for optimal adherence
 */
export interface ReminderSettings {
  enabled: boolean
  advanceMinutes: number
  repeatCount: number
  repeatIntervalMinutes: number
  notificationType: 'push' | 'email' | 'sms' | 'all'
  snoozeEnabled: boolean
  snoozeMinutes: number
}

/**
 * Patient lifestyle preferences for schedule optimization
 */
export interface LifestylePreferences {
  wakeUpTime: string // HH:MM
  bedTime: string // HH:MM
  mealTimes: {
    breakfast: string
    lunch: string
    dinner: string
  }
  workSchedule?: {
    startTime: string
    endTime: string
    daysOfWeek: number[]
  }
  preferredReminderTimes: string[]
  avoidTimes: string[]
  timezone: string
  adherenceHistory: {
    bestTimes: string[]
    worstTimes: string[]
    missedDosePatterns: string[]
  }
}

/**
 * Comprehensive Schedule Generator Service
 * 
 * Analyzes medication prescriptions and creates optimal dosing schedules
 * with conflict resolution, adherence optimization, and lifestyle consideration
 */
export class ScheduleGenerator {
  private optimalTimePeriods: OptimalTimePeriod[] = [
    {
      startTime: '06:00',
      endTime: '08:00',
      label: 'Early Morning',
      priority: 1,
      mealRelation: 'empty_stomach',
      description: 'Best for medications requiring empty stomach'
    },
    {
      startTime: '08:00',
      endTime: '09:00',
      label: 'Breakfast',
      priority: 2,
      mealRelation: 'with_meal',
      description: 'Optimal for medications taken with breakfast'
    },
    {
      startTime: '12:00',
      endTime: '13:00',
      label: 'Lunch',
      priority: 2,
      mealRelation: 'with_meal',
      description: 'Optimal for medications taken with lunch'
    },
    {
      startTime: '18:00',
      endTime: '19:00',
      label: 'Dinner',
      priority: 2,
      mealRelation: 'with_meal',
      description: 'Optimal for medications taken with dinner'
    },
    {
      startTime: '21:00',
      endTime: '22:00',
      label: 'Bedtime',
      priority: 3,
      mealRelation: 'any',
      description: 'Good for once-daily medications and sleep aids'
    },
    {
      startTime: '14:00',
      endTime: '15:00',
      label: 'Afternoon',
      priority: 4,
      mealRelation: 'any',
      description: 'Flexible time for additional doses'
    }
  ]

  /**
   * Generate optimal schedules for a list of medications
   */
  async generateOptimalSchedules(
    medications: Medication[],
    lifestylePreferences: LifestylePreferences
  ): Promise<OptimizedSchedule[]> {
    console.log('📅 Generating optimal schedules for', medications.length, 'medications')
    
    const optimizedSchedules: OptimizedSchedule[] = []
    const allSchedules: GeneratedSchedule[] = []
    
    // 1. Analyze each medication and create dosing requirements
    const dosingRequirements = await this.analyzeDosingRequirements(medications)
    
    // 2. Check for medication interactions
    const interactions = await this.checkMedicationInteractions(medications)
    
    // 3. Generate individual schedules
    for (const requirement of dosingRequirements) {
      const schedule = await this.generateMedicationSchedule(requirement, lifestylePreferences)
      optimizedSchedules.push(schedule)
      allSchedules.push(...schedule.schedules)
    }
    
    // 4. Detect and resolve conflicts
    const conflicts = this.detectScheduleConflicts(allSchedules, interactions)
    
    // 5. Optimize schedules based on conflicts
    const optimizedSchedulesWithConflicts = this.resolveConflicts(
      optimizedSchedules,
      conflicts,
      lifestylePreferences
    )
    
    // 6. Calculate adherence scores
    const finalSchedules = await this.calculateAdherenceScores(
      optimizedSchedulesWithConflicts,
      lifestylePreferences
    )
    
    console.log('✅ Generated', finalSchedules.length, 'optimized schedules')
    return finalSchedules
  }

  /**
   * Analyze medication dosing requirements
   */
  private async analyzeDosingRequirements(medications: Medication[]): Promise<DosingRequirements[]> {
    const requirements: DosingRequirements[] = []
    
    for (const medication of medications) {
      const frequency = medication.frequency.toLowerCase()
      const instructions = medication.instructions.toLowerCase()
      
      // Parse frequency to determine doses per day
      const totalDosesPerDay = this.parseFrequencyToDoses(frequency)
      
      // Determine meal requirements from instructions
      const mealRequirements = this.parseMealRequirements(instructions)
      
      // Calculate minimum interval between doses
      const minIntervalHours = this.calculateMinInterval(totalDosesPerDay)
      const maxIntervalHours = 24 / totalDosesPerDay
      
      // Check for variable dosing (e.g., insulin)
      const variableDosing = this.parseVariableDosing(medication)
      
      // Check if medication is "as needed"
      const isAsNeeded = this.isAsNeededMedication(instructions, frequency)
      
      requirements.push({
        medicationId: medication.id,
        medication,
        frequency,
        totalDosesPerDay,
        mealRequirements,
        minIntervalHours,
        maxIntervalHours,
        preferredTimes: this.extractPreferredTimes(instructions),
        avoidTimes: this.extractAvoidTimes(instructions),
        specialInstructions: this.extractSpecialInstructions(instructions),
        isAsNeeded,
        variableDosing
      })
    }
    
    return requirements
  }

  /**
   * Parse frequency string to number of doses per day
   */
  private parseFrequencyToDoses(frequency: string): number {
    const frequencyMap: Record<string, number> = {
      'once daily': 1,
      'twice daily': 2,
      'three times daily': 3,
      'four times daily': 4,
      'every 6 hours': 4,
      'every 8 hours': 3,
      'every 12 hours': 2,
      'every 4 hours': 6,
      'as needed': 1,
      'prn': 1,
      'daily': 1,
      'bid': 2,
      'tid': 3,
      'qid': 4
    }
    
    for (const [pattern, doses] of Object.entries(frequencyMap)) {
      if (frequency.includes(pattern)) {
        return doses
      }
    }
    
    // Default to once daily if pattern not recognized
    return 1
  }

  /**
   * Parse meal requirements from medication instructions
   */
  private parseMealRequirements(instructions: string): 'before_meal' | 'with_meal' | 'after_meal' | 'empty_stomach' | 'any' {
    if (instructions.includes('empty stomach') || instructions.includes('fasting')) {
      return 'empty_stomach'
    }
    if (instructions.includes('with food') || instructions.includes('with meal')) {
      return 'with_meal'
    }
    if (instructions.includes('before meal') || instructions.includes('before food')) {
      return 'before_meal'
    }
    if (instructions.includes('after meal') || instructions.includes('after food')) {
      return 'after_meal'
    }
    return 'any'
  }

  /**
   * Calculate minimum interval between doses
   */
  private calculateMinInterval(dosesPerDay: number): number {
    if (dosesPerDay === 1) return 12 // At least 12 hours between doses
    if (dosesPerDay === 2) return 8  // At least 8 hours between doses
    if (dosesPerDay === 3) return 6  // At least 6 hours between doses
    if (dosesPerDay === 4) return 4  // At least 4 hours between doses
    return 24 / dosesPerDay
  }

  /**
   * Parse variable dosing information (e.g., insulin)
   */
  private parseVariableDosing(medication: Medication): any {
    const instructions = medication.instructions.toLowerCase()
    const name = medication.name.toLowerCase()
    
    // Check for insulin or other variable dosing medications
    if (name.includes('insulin') || instructions.includes('adjust dose') || instructions.includes('variable')) {
      return {
        minDose: 1,
        maxDose: 50,
        unit: 'units',
        adjustmentFactors: ['blood glucose', 'carbohydrate intake', 'physical activity']
      }
    }
    
    return undefined
  }

  /**
   * Check if medication is "as needed"
   */
  private isAsNeededMedication(instructions: string, frequency: string): boolean {
    return instructions.includes('as needed') || 
           instructions.includes('prn') || 
           frequency.includes('as needed') ||
           frequency.includes('prn')
  }

  /**
   * Extract preferred times from instructions
   */
  private extractPreferredTimes(instructions: string): string[] {
    const times: string[] = []
    const timePatterns = [
      /(\d{1,2}):(\d{2})\s*(am|pm)/gi,
      /(\d{1,2})\s*(am|pm)/gi,
      /(\d{1,2})h(\d{2})/gi
    ]
    
    for (const pattern of timePatterns) {
      const matches = instructions.match(pattern)
      if (matches) {
        times.push(...matches.map(this.normalizeTime))
      }
    }
    
    return times
  }

  /**
   * Extract times to avoid from instructions
   */
  private extractAvoidTimes(instructions: string): string[] {
    const avoidTimes: string[] = []
    
    if (instructions.includes('avoid evening') || instructions.includes('not at night')) {
      avoidTimes.push('18:00', '19:00', '20:00', '21:00', '22:00')
    }
    
    if (instructions.includes('avoid morning')) {
      avoidTimes.push('06:00', '07:00', '08:00', '09:00')
    }
    
    return avoidTimes
  }

  /**
   * Extract special instructions
   */
  private extractSpecialInstructions(instructions: string): string[] {
    const specialInstructions: string[] = []
    
    if (instructions.includes('take with water')) {
      specialInstructions.push('Take with full glass of water')
    }
    
    if (instructions.includes('avoid alcohol')) {
      specialInstructions.push('Avoid alcohol while taking this medication')
    }
    
    if (instructions.includes('avoid driving')) {
      specialInstructions.push('Avoid driving or operating machinery')
    }
    
    return specialInstructions
  }

  /**
   * Generate schedule for a single medication
   */
  private async generateMedicationSchedule(
    requirement: DosingRequirements,
    lifestylePreferences: LifestylePreferences
  ): Promise<OptimizedSchedule> {
    const schedules: GeneratedSchedule[] = []
    const conflicts: ScheduleConflict[] = []
    const optimizationNotes: string[] = []
    
    if (requirement.isAsNeeded) {
      // Handle "as needed" medications
      schedules.push(this.createAsNeededSchedule(requirement))
    } else if (requirement.variableDosing) {
      // Handle variable dosing medications
      schedules.push(...this.createVariableDosingSchedules(requirement, lifestylePreferences))
    } else {
      // Handle regular fixed dosing
      schedules.push(...this.createFixedDosingSchedules(requirement, lifestylePreferences))
    }
    
    return {
      medicationId: requirement.medicationId,
      medication: requirement.medication,
      schedules,
      conflicts,
      adherenceScore: 0, // Will be calculated later
      optimizationNotes,
      alternativeSchedules: []
    }
  }

  /**
   * Create schedule for "as needed" medications
   */
  private createAsNeededSchedule(requirement: DosingRequirements): GeneratedSchedule {
    return {
      id: `${requirement.medicationId}-as-needed`,
      time: '09:00', // Default reminder time
      dosage: 1,
      unit: 'dose',
      mealRelation: requirement.mealRequirements,
      instructions: requirement.specialInstructions.join('. '),
      priority: 'low',
      reminderSettings: {
        enabled: true,
        advanceMinutes: 0,
        repeatCount: 3,
        repeatIntervalMinutes: 60,
        notificationType: 'push',
        snoozeEnabled: true,
        snoozeMinutes: 30
      },
      isAsNeeded: true
    }
  }

  /**
   * Create schedules for variable dosing medications
   */
  private createVariableDosingSchedules(
    requirement: DosingRequirements,
    lifestylePreferences: LifestylePreferences
  ): GeneratedSchedule[] {
    const schedules: GeneratedSchedule[] = []
    
    // For insulin, typically 2-4 doses per day
    const dosesPerDay = Math.min(requirement.totalDosesPerDay, 4)
    
    for (let i = 0; i < dosesPerDay; i++) {
      const time = this.calculateOptimalTime(i, dosesPerDay, lifestylePreferences, requirement)
      
      schedules.push({
        id: `${requirement.medicationId}-dose-${i + 1}`,
        time,
        dosage: requirement.variableDosing!.minDose,
        unit: requirement.variableDosing!.unit,
        mealRelation: requirement.mealRequirements,
        instructions: `Adjust dose based on: ${requirement.variableDosing!.adjustmentFactors.join(', ')}`,
        priority: 'high',
        reminderSettings: {
          enabled: true,
          advanceMinutes: 15,
          repeatCount: 2,
          repeatIntervalMinutes: 30,
          notificationType: 'all',
          snoozeEnabled: false,
          snoozeMinutes: 0
        },
        isAsNeeded: false,
        variableDosing: {
          currentDose: requirement.variableDosing!.minDose,
          adjustmentReason: 'Initial dose'
        }
      })
    }
    
    return schedules
  }

  /**
   * Create schedules for fixed dosing medications
   */
  private createFixedDosingSchedules(
    requirement: DosingRequirements,
    lifestylePreferences: LifestylePreferences
  ): GeneratedSchedule[] {
    const schedules: GeneratedSchedule[] = []
    
    for (let i = 0; i < requirement.totalDosesPerDay; i++) {
      const time = this.calculateOptimalTime(i, requirement.totalDosesPerDay, lifestylePreferences, requirement)
      
      schedules.push({
        id: `${requirement.medicationId}-dose-${i + 1}`,
        time,
        dosage: 1, // Default to 1, should be parsed from medication
        unit: 'tablet', // Default unit
        mealRelation: requirement.mealRequirements,
        instructions: requirement.specialInstructions.join('. '),
        priority: this.calculatePriority(requirement, i),
        reminderSettings: this.calculateReminderSettings(requirement, i),
        isAsNeeded: false
      })
    }
    
    return schedules
  }

  /**
   * Calculate optimal time for a dose
   */
  private calculateOptimalTime(
    doseIndex: number,
    totalDoses: number,
    lifestylePreferences: LifestylePreferences,
    requirement: DosingRequirements
  ): string {
    // Use preferred times if available
    if (requirement.preferredTimes.length > 0 && doseIndex < requirement.preferredTimes.length) {
      return requirement.preferredTimes[doseIndex]
    }
    
    // Calculate based on meal requirements and lifestyle
    if (requirement.mealRequirements === 'with_meal') {
      const mealTimes = [
        lifestylePreferences.mealTimes.breakfast,
        lifestylePreferences.mealTimes.lunch,
        lifestylePreferences.mealTimes.dinner
      ]
      
      if (doseIndex < mealTimes.length) {
        return mealTimes[doseIndex]
      }
    }
    
    // Default time distribution
    const defaultTimes = ['08:00', '12:00', '18:00', '22:00']
    return defaultTimes[doseIndex] || '08:00'
  }

  /**
   * Calculate priority for a dose
   */
  private calculatePriority(requirement: DosingRequirements, doseIndex: number): 'high' | 'medium' | 'low' {
    // High priority for critical medications
    if (requirement.medication.category?.toLowerCase().includes('critical')) {
      return 'high'
    }
    
    // High priority for first dose of the day
    if (doseIndex === 0) {
      return 'high'
    }
    
    // Medium priority for other doses
    return 'medium'
  }

  /**
   * Calculate reminder settings for a dose
   */
  private calculateReminderSettings(requirement: DosingRequirements, doseIndex: number): ReminderSettings {
    return {
      enabled: true,
      advanceMinutes: doseIndex === 0 ? 30 : 15, // More advance notice for first dose
      repeatCount: 2,
      repeatIntervalMinutes: 30,
      notificationType: 'push',
      snoozeEnabled: true,
      snoozeMinutes: 15
    }
  }

  /**
   * Check for medication interactions
   */
  private async checkMedicationInteractions(medications: Medication[]): Promise<MedicationInteraction[]> {
    try {
      const medicationIds = medications.map(med => med.id)
      return await medicationApi.checkMedicationInteractions(medicationIds)
    } catch (error) {
      console.warn('Failed to check medication interactions:', error)
      return []
    }
  }

  /**
   * Detect schedule conflicts
   */
  private detectScheduleConflicts(
    schedules: GeneratedSchedule[],
    interactions: MedicationInteraction[]
  ): ScheduleConflict[] {
    const conflicts: ScheduleConflict[] = []
    
    // Check for timing overlaps
    for (let i = 0; i < schedules.length; i++) {
      for (let j = i + 1; j < schedules.length; j++) {
        const conflict = this.checkTimingConflict(schedules[i], schedules[j])
        if (conflict) {
          conflicts.push(conflict)
        }
      }
    }
    
    // Check for medication interactions
    for (const interaction of interactions) {
      const affectedSchedules = schedules.filter(schedule => 
        interaction.medications.includes(schedule.medicationId)
      )
      
      if (affectedSchedules.length > 1) {
        conflicts.push({
          type: 'interaction',
          severity: this.mapInteractionSeverity(interaction.severity),
          description: interaction.description,
          affectedMedications: interaction.medications,
          recommendations: [interaction.recommendations]
        })
      }
    }
    
    return conflicts
  }

  /**
   * Check for timing conflicts between two schedules
   */
  private checkTimingConflict(schedule1: GeneratedSchedule, schedule2: GeneratedSchedule): ScheduleConflict | null {
    const time1 = this.parseTime(schedule1.time)
    const time2 = this.parseTime(schedule2.time)
    
    const diffMinutes = Math.abs(time1 - time2)
    
    if (diffMinutes < 30) { // Less than 30 minutes apart
      return {
        type: 'timing_overlap',
        severity: 'medium',
        description: `Medications scheduled too close together: ${schedule1.time} and ${schedule2.time}`,
        affectedMedications: [schedule1.medicationId, schedule2.medicationId],
        recommendations: [
          'Consider spacing doses at least 30 minutes apart',
          'Take one medication 15 minutes before the other'
        ],
        alternativeTiming: [
          this.addMinutes(schedule1.time, 30),
          this.addMinutes(schedule2.time, 30)
        ]
      }
    }
    
    return null
  }

  /**
   * Resolve schedule conflicts
   */
  private resolveConflicts(
    schedules: OptimizedSchedule[],
    conflicts: ScheduleConflict[],
    lifestylePreferences: LifestylePreferences
  ): OptimizedSchedule[] {
    const resolvedSchedules = [...schedules]
    
    for (const conflict of conflicts) {
      if (conflict.type === 'timing_overlap') {
        this.resolveTimingConflict(resolvedSchedules, conflict, lifestylePreferences)
      } else if (conflict.type === 'interaction') {
        this.resolveInteractionConflict(resolvedSchedules, conflict)
      }
    }
    
    return resolvedSchedules
  }

  /**
   * Resolve timing conflicts by adjusting schedules
   */
  private resolveTimingConflict(
    schedules: OptimizedSchedule[],
    conflict: ScheduleConflict,
    lifestylePreferences: LifestylePreferences
  ): void {
    // Find affected schedules
    const affectedSchedules = schedules.filter(schedule =>
      conflict.affectedMedications.includes(schedule.medicationId)
    )
    
    if (affectedSchedules.length >= 2) {
      const schedule1 = affectedSchedules[0]
      const schedule2 = affectedSchedules[1]
      
      // Adjust the second schedule by 30 minutes
      if (schedule2.schedules.length > 0) {
        const adjustedTime = this.addMinutes(schedule2.schedules[0].time, 30)
        schedule2.schedules[0].time = adjustedTime
        
        // Add note about adjustment
        schedule2.optimizationNotes.push(
          `Schedule adjusted to ${adjustedTime} to avoid conflict with ${schedule1.medication.name}`
        )
      }
    }
  }

  /**
   * Resolve interaction conflicts
   */
  private resolveInteractionConflict(
    schedules: OptimizedSchedule[],
    conflict: ScheduleConflict
  ): void {
    // Add interaction warnings to affected schedules
    for (const schedule of schedules) {
      if (conflict.affectedMedications.includes(schedule.medicationId)) {
        schedule.conflicts.push(conflict)
        schedule.optimizationNotes.push(
          `⚠️ Interaction detected: ${conflict.description}`
        )
      }
    }
  }

  /**
   * Calculate adherence scores based on lifestyle preferences
   */
  private async calculateAdherenceScores(
    schedules: OptimizedSchedule[],
    lifestylePreferences: LifestylePreferences
  ): Promise<OptimizedSchedule[]> {
    for (const schedule of schedules) {
      let adherenceScore = 100
      
      // Check if schedules align with patient's best times
      for (const dose of schedule.schedules) {
        const timeScore = this.calculateTimeAlignmentScore(dose.time, lifestylePreferences)
        adherenceScore = Math.min(adherenceScore, timeScore)
      }
      
      // Check for conflicts that might affect adherence
      if (schedule.conflicts.length > 0) {
        adherenceScore -= schedule.conflicts.length * 10
      }
      
      // Ensure score doesn't go below 0
      schedule.adherenceScore = Math.max(0, adherenceScore)
    }
    
    return schedules
  }

  /**
   * Calculate how well a time aligns with patient's preferences
   */
  private calculateTimeAlignmentScore(time: string, preferences: LifestylePreferences): number {
    const timeMinutes = this.parseTime(time)
    
    // Check if time is in patient's best times
    for (const bestTime of preferences.adherenceHistory.bestTimes) {
      const bestTimeMinutes = this.parseTime(bestTime)
      if (Math.abs(timeMinutes - bestTimeMinutes) < 60) { // Within 1 hour
        return 100
      }
    }
    
    // Check if time is in patient's worst times
    for (const worstTime of preferences.adherenceHistory.worstTimes) {
      const worstTimeMinutes = this.parseTime(worstTime)
      if (Math.abs(timeMinutes - worstTimeMinutes) < 60) { // Within 1 hour
        return 50
      }
    }
    
    // Check if time conflicts with work schedule
    if (preferences.workSchedule) {
      const workStart = this.parseTime(preferences.workSchedule.startTime)
      const workEnd = this.parseTime(preferences.workSchedule.endTime)
      
      if (timeMinutes >= workStart && timeMinutes <= workEnd) {
        return 70 // Slightly lower score during work hours
      }
    }
    
    return 85 // Default good score
  }

  /**
   * Generate medication calendar with visual schedule representation
   */
  generateMedicationCalendar(
    schedules: OptimizedSchedule[],
    startDate: Date = new Date(),
    days: number = 7
  ): MedicationCalendar {
    const calendar: MedicationCalendar = {
      startDate: startDate.toISOString(),
      endDate: new Date(startDate.getTime() + days * 24 * 60 * 60 * 1000).toISOString(),
      days: []
    }
    
    for (let i = 0; i < days; i++) {
      const currentDate = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000)
      const daySchedule = this.generateDaySchedule(schedules, currentDate)
      calendar.days.push(daySchedule)
    }
    
    return calendar
  }

  /**
   * Generate schedule for a specific day
   */
  private generateDaySchedule(schedules: OptimizedSchedule[], date: Date): DaySchedule {
    const daySchedule: DaySchedule = {
      date: date.toISOString(),
      timeSlots: this.createTimeSlots(),
      summary: {
        totalDoses: 0,
        criticalDoses: 0,
        asNeededDoses: 0,
        conflicts: []
      }
    }
    
    // Populate time slots with medications
    for (const schedule of schedules) {
      for (const dose of schedule.schedules) {
        const timeSlot = this.findTimeSlot(daySchedule.timeSlots, dose.time)
        if (timeSlot) {
          timeSlot.medications.push({
            medicationId: schedule.medicationId,
            medication: schedule.medication,
            dosage: dose.dosage,
            unit: dose.unit,
            instructions: dose.instructions,
            priority: dose.priority,
            isAsNeeded: dose.isAsNeeded
          })
          
          daySchedule.summary.totalDoses++
          if (dose.priority === 'high') {
            daySchedule.summary.criticalDoses++
          }
          if (dose.isAsNeeded) {
            daySchedule.summary.asNeededDoses++
          }
        }
      }
    }
    
    return daySchedule
  }

  /**
   * Create time slots for the day
   */
  private createTimeSlots(): TimeSlot[] {
    const slots: TimeSlot[] = []
    
    for (let hour = 6; hour <= 22; hour++) {
      slots.push({
        time: `${hour.toString().padStart(2, '0')}:00`,
        medications: [],
        mealTime: this.getMealTime(hour)
      })
    }
    
    return slots
  }

  /**
   * Find appropriate time slot for a given time
   */
  private findTimeSlot(timeSlots: TimeSlot[], time: string): TimeSlot | null {
    const targetHour = parseInt(time.split(':')[0])
    
    for (const slot of timeSlots) {
      const slotHour = parseInt(slot.time.split(':')[0])
      if (slotHour === targetHour) {
        return slot
      }
    }
    
    return null
  }

  /**
   * Get meal time for a given hour
   */
  private getMealTime(hour: number): 'breakfast' | 'lunch' | 'dinner' | null {
    if (hour >= 7 && hour <= 9) return 'breakfast'
    if (hour >= 11 && hour <= 13) return 'lunch'
    if (hour >= 17 && hour <= 19) return 'dinner'
    return null
  }

  /**
   * Utility functions
   */
  private parseTime(time: string): number {
    const [hours, minutes] = time.split(':').map(Number)
    return hours * 60 + minutes
  }

  private addMinutes(time: string, minutes: number): string {
    const totalMinutes = this.parseTime(time) + minutes
    const hours = Math.floor(totalMinutes / 60) % 24
    const mins = totalMinutes % 60
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
  }

  private normalizeTime(timeString: string): string {
    // Convert various time formats to HH:MM
    const match = timeString.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)?/i)
    if (match) {
      let hours = parseInt(match[1])
      const minutes = match[2] ? parseInt(match[2]) : 0
      const period = match[3]?.toLowerCase()
      
      if (period === 'pm' && hours !== 12) hours += 12
      if (period === 'am' && hours === 12) hours = 0
      
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
    }
    return '08:00' // Default fallback
  }

  private mapInteractionSeverity(severity: string): 'low' | 'medium' | 'high' | 'critical' {
    switch (severity.toLowerCase()) {
      case 'low': return 'low'
      case 'moderate': return 'medium'
      case 'high': return 'high'
      case 'contraindicated': return 'critical'
      default: return 'medium'
    }
  }
}

/**
 * Calendar interfaces for visual schedule representation
 */
export interface MedicationCalendar {
  startDate: string
  endDate: string
  days: DaySchedule[]
}

export interface DaySchedule {
  date: string
  timeSlots: TimeSlot[]
  summary: DaySummary
}

export interface TimeSlot {
  time: string
  medications: ScheduledMedication[]
  mealTime: 'breakfast' | 'lunch' | 'dinner' | null
}

export interface ScheduledMedication {
  medicationId: string
  medication: Medication
  dosage: number
  unit: string
  instructions: string
  priority: 'high' | 'medium' | 'low'
  isAsNeeded: boolean
}

export interface DaySummary {
  totalDoses: number
  criticalDoses: number
  asNeededDoses: number
  conflicts: ScheduleConflict[]
}

// Export singleton instance
export const scheduleGenerator = new ScheduleGenerator() 