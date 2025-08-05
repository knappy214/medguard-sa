# Schedule Generator Service

## Overview

The Schedule Generator Service is a comprehensive medication scheduling system that analyzes prescription data and creates optimal dosing schedules. It handles complex scenarios including variable dosing medications (like insulin), medication interactions, adherence optimization, and lifestyle considerations.

## Key Features

### 1. **Prescription Analysis & Optimal Dosing**
- Analyzes medication frequency patterns (once daily, twice daily, etc.)
- Parses meal requirements (with food, empty stomach, before/after meals)
- Extracts preferred and avoid times from instructions
- Handles special instructions and contraindications

### 2. **Complex Medication Support**
- **Variable Dosing**: Supports insulin and other medications with adjustable doses
- **As Needed (PRN)**: Tracks medications taken as needed with usage monitoring
- **Multiple Daily Doses**: Distributes doses optimally across the day
- **Meal Timing**: Aligns medications with patient meal schedules

### 3. **Conflict Resolution**
- **Timing Conflicts**: Detects medications scheduled too close together
- **Medication Interactions**: Identifies potential drug interactions
- **Meal Conflicts**: Ensures proper timing for food-dependent medications
- **Dose Spacing**: Maintains appropriate intervals between doses

### 4. **Adherence Optimization**
- **Lifestyle Integration**: Considers patient's daily routine and preferences
- **Work Schedule**: Avoids medication times during work hours if needed
- **Best/Worst Times**: Uses historical adherence data to optimize timing
- **Adherence Scoring**: Calculates likelihood of medication adherence

### 5. **Visual Calendar Generation**
- **Daily Schedules**: Creates hour-by-hour medication schedules
- **Weekly Views**: Generates 7-day medication calendars
- **Conflict Highlighting**: Shows potential issues in the schedule
- **Summary Statistics**: Provides daily dose counts and critical medication tracking

## Core Interfaces

### `LifestylePreferences`
```typescript
interface LifestylePreferences {
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
```

### `OptimizedSchedule`
```typescript
interface OptimizedSchedule {
  medicationId: string
  medication: Medication
  schedules: GeneratedSchedule[]
  conflicts: ScheduleConflict[]
  adherenceScore: number
  optimizationNotes: string[]
  alternativeSchedules: GeneratedSchedule[][]
}
```

### `GeneratedSchedule`
```typescript
interface GeneratedSchedule {
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
```

## Usage Examples

### Basic Schedule Generation
```typescript
import { scheduleGenerator } from '@/services/scheduleGenerator'

const medications = [
  {
    id: '1',
    name: 'Metformin',
    dosage: '500mg',
    frequency: 'Twice daily',
    instructions: 'Take with food to reduce stomach upset',
    // ... other medication properties
  }
]

const lifestylePreferences = {
  wakeUpTime: '07:00',
  bedTime: '22:00',
  mealTimes: {
    breakfast: '08:00',
    lunch: '12:30',
    dinner: '18:30'
  },
  // ... other lifestyle preferences
}

const optimizedSchedules = await scheduleGenerator.generateOptimalSchedules(
  medications,
  lifestylePreferences
)
```

### Insulin Schedule with Variable Dosing
```typescript
const insulinMedications = [
  {
    id: 'insulin-1',
    name: 'NovoRapid Insulin',
    dosage: 'Variable',
    frequency: 'Three times daily',
    instructions: 'Adjust dose based on blood glucose and carbohydrate intake',
    // ... other properties
  }
]

const insulinSchedules = await scheduleGenerator.generateOptimalSchedules(
  insulinMedications,
  lifestylePreferences
)

// Check for variable dosing features
insulinSchedules.forEach(schedule => {
  schedule.schedules.forEach(dose => {
    if (dose.variableDosing) {
      console.log('Variable dosing:', dose.variableDosing)
    }
  })
})
```

### Generate Medication Calendar
```typescript
const schedules = await scheduleGenerator.generateOptimalSchedules(
  medications,
  lifestylePreferences
)

// Generate 7-day calendar
const calendar = scheduleGenerator.generateMedicationCalendar(schedules, new Date(), 7)

// Access daily schedules
calendar.days.forEach(day => {
  console.log(`Date: ${day.date}`)
  console.log(`Total doses: ${day.summary.totalDoses}`)
  console.log(`Critical doses: ${day.summary.criticalDoses}`)
  
  // Show medications by time slot
  day.timeSlots.forEach(slot => {
    if (slot.medications.length > 0) {
      console.log(`${slot.time}: ${slot.medications.map(med => 
        `${med.medication.name} (${med.dosage}${med.unit})`
      ).join(', ')}`)
    }
  })
})
```

## Advanced Features

### 1. **Conflict Detection & Resolution**

The service automatically detects and resolves various types of conflicts:

- **Timing Overlaps**: Medications scheduled within 30 minutes of each other
- **Medication Interactions**: Based on drug interaction databases
- **Meal Conflicts**: Ensuring proper timing for food-dependent medications
- **Dose Spacing**: Maintaining appropriate intervals between doses

```typescript
// Conflicts are automatically detected and included in the schedule
optimizedSchedules.forEach(schedule => {
  if (schedule.conflicts.length > 0) {
    console.log(`Conflicts for ${schedule.medication.name}:`, schedule.conflicts)
  }
})
```

### 2. **Adherence Optimization**

The service calculates adherence scores based on:
- Alignment with patient's best adherence times
- Work schedule conflicts
- Historical missed dose patterns
- Schedule complexity

```typescript
optimizedSchedules.forEach(schedule => {
  console.log(`${schedule.medication.name} adherence score: ${schedule.adherenceScore}%`)
  
  if (schedule.adherenceScore < 80) {
    console.log('Low adherence risk - consider schedule adjustments')
  }
})
```

### 3. **Variable Dosing Support**

For medications like insulin that require dose adjustments:

```typescript
const variableDosingSchedule = {
  id: 'insulin-dose-1',
  time: '08:00',
  dosage: 10,
  unit: 'units',
  variableDosing: {
    currentDose: 10,
    adjustmentReason: 'Initial dose'
  },
  instructions: 'Adjust dose based on: blood glucose, carbohydrate intake, physical activity'
}
```

### 4. **As Needed (PRN) Medications**

Special handling for medications taken as needed:

```typescript
const prnSchedule = {
  id: 'albuterol-as-needed',
  time: '09:00',
  dosage: 1,
  unit: 'dose',
  isAsNeeded: true,
  reminderSettings: {
    enabled: true,
    advanceMinutes: 0,
    repeatCount: 3,
    repeatIntervalMinutes: 60,
    notificationType: 'push',
    snoozeEnabled: true,
    snoozeMinutes: 30
  }
}
```

## Integration with Existing Services

### Medication API Integration
The schedule generator integrates with the existing `medicationApi` service:

```typescript
// Check for medication interactions
const interactions = await medicationApi.checkMedicationInteractions(medicationIds)

// Get adherence tracking data
const adherenceTracking = await medicationApi.getAdherenceTracking(medicationId)
```

### Backend Schedule Creation
Generated schedules can be saved to the backend:

```typescript
// Create medication schedules in the backend
const backendSchedules = await medicationApi.createMedicationSchedules(
  medicationId,
  scheduleData
)
```

## Error Handling

The service includes comprehensive error handling:

```typescript
try {
  const schedules = await scheduleGenerator.generateOptimalSchedules(
    medications,
    lifestylePreferences
  )
} catch (error) {
  console.error('Failed to generate schedules:', error)
  
  // Handle specific error types
  if (error.message.includes('interaction')) {
    // Handle interaction errors
  } else if (error.message.includes('conflict')) {
    // Handle conflict resolution errors
  }
}
```

## Performance Considerations

- **Batch Processing**: Handles multiple medications efficiently
- **Caching**: Caches interaction data to avoid repeated API calls
- **Optimization**: Uses efficient algorithms for schedule generation
- **Memory Management**: Minimizes memory usage for large medication lists

## Testing

Run the example scenarios to test the service:

```typescript
import { runAllExamples } from '@/services/scheduleGenerator.example'

// Run all examples
await runAllExamples()

// Or run individual examples
import { exampleInsulinSchedule } from '@/services/scheduleGenerator.example'
await exampleInsulinSchedule()
```

## Future Enhancements

1. **Machine Learning Integration**: Use ML to predict optimal dosing times based on historical data
2. **Real-time Adjustments**: Dynamic schedule adjustments based on patient feedback
3. **Integration with Health Devices**: Connect with glucose monitors, blood pressure cuffs, etc.
4. **Advanced Analytics**: Detailed adherence analytics and trend analysis
5. **Multi-language Support**: Support for Afrikaans and other languages
6. **Offline Capability**: Generate schedules without internet connectivity

## Contributing

When contributing to the schedule generator:

1. **Follow TypeScript best practices**: Use strict typing and proper interfaces
2. **Add comprehensive tests**: Include unit tests for new features
3. **Update documentation**: Keep this README and examples current
4. **Consider edge cases**: Handle unusual medication scenarios
5. **Performance testing**: Ensure new features don't impact performance

## Support

For questions or issues with the schedule generator:

1. Check the examples in `scheduleGenerator.example.ts`
2. Review the TypeScript interfaces for proper data structures
3. Test with the provided example scenarios
4. Check the medication API integration points 