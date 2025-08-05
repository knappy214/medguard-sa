/**
 * Prescription Parser Utility
 * 
 * Comprehensive utility for parsing prescription text and converting it into
 * structured medication data for the MedGuard SA system.
 * 
 * Features:
 * - Regex patterns for common prescription formats
 * - Medication abbreviation mapping
 * - Dosage instruction parsing
 * - ICD-10 code extraction and mapping
 * - Medication type identification
 * - Quantity and timing parsing
 * - Repeat information extraction
 * - Data validation against known databases
 * - Standardized medication object creation
 */

import type { Medication, MedicationFormData, ICD10Code } from '@/types/medication'

// ============================================================================
// REGEX PATTERNS FOR PRESCRIPTION PARSING
// ============================================================================

export const PRESCRIPTION_PATTERNS = {
  // Medication name patterns (brand names, generic names)
  MEDICATION_NAME: /([A-Z][A-Z0-9\s\-]+)(?:\s+(?:tablets?|capsules?|injection|suspension|syrup|drops|cream|ointment|patch|inhaler))?/gi,
  
  // Dosage patterns
  DOSAGE: /(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|iu|meq|mmol|%|tablets?|capsules?|puffs?|drops?|applications?)/gi,
  
  // Frequency patterns
  FREQUENCY: /(once|twice|three times|four times|daily|weekly|monthly|every\s+\d+\s+(?:hours?|days?|weeks?|months?))/gi,
  
  // Timing patterns
  TIMING: /(morning|noon|afternoon|evening|night|bedtime|before\s+(?:breakfast|lunch|dinner|meals?)|after\s+(?:breakfast|lunch|dinner|meals?)|with\s+(?:breakfast|lunch|dinner|meals?))/gi,
  
  // Quantity patterns
  QUANTITY: /(?:x\s*|quantity\s*:?\s*|qty\s*:?\s*|pack\s+of\s*|box\s+of\s*)(\d+)/gi,
  
  // Repeat patterns
  REPEATS: /(?:repeat\s*|refill\s*|renewal\s*|\+?\s*)(\d+)\s*(?:repeats?|refills?|renewals?|times?)/gi,
  
  // ICD-10 code patterns
  ICD10_CODE: /([A-Z]\d{2}(?:\.\d{1,2})?)/g,
  
  // Prescription number patterns
  PRESCRIPTION_NUMBER: /(?:prescription\s*#?\s*|script\s*#?\s*|rx\s*#?\s*|ref\s*#?\s*)([A-Z0-9\-]+)/gi,
  
  // Doctor/physician patterns
  DOCTOR: /(?:dr\.?\s*|doctor\s*|physician\s*|prescribed\s+by\s*)([A-Z][a-z]+\s+[A-Z][a-z]+)/gi,
  
  // Date patterns
  DATE: /(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})/g,
  
  // Instructions patterns
  INSTRUCTIONS: /(?:take\s*|use\s*|apply\s*|inhale\s*|inject\s*)(.+?)(?=\s*(?:morning|noon|night|daily|weekly|$))/gi,
  
  // Expiry patterns
  EXPIRY: /(?:expires?\s*|expiry\s*|exp\s*|valid\s+until\s*)(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})/gi
}

// ============================================================================
// MEDICATION ABBREVIATION MAPPING
// ============================================================================

export const MEDICATION_ABBREVIATIONS: Record<string, string> = {
  // Insulin types
  'NOVORAPID': 'Insulin aspart',
  'NOVOLOG': 'Insulin aspart',
  'LANTUS': 'Insulin glargine',
  'TOUJEO': 'Insulin glargine',
  'LEVEMIR': 'Insulin detemir',
  'TRESIBA': 'Insulin degludec',
  'HUMALOG': 'Insulin lispro',
  'HUMULIN': 'Insulin human',
  'APIDRA': 'Insulin glulisine',
  
  // Common diabetes medications
  'METFORMIN': 'Metformin',
  'GLUCOPHAGE': 'Metformin',
  'JANUVIA': 'Sitagliptin',
  'ONGLYZA': 'Saxagliptin',
  'TRADJENTA': 'Linagliptin',
  'GLIPIZIDE': 'Glipizide',
  'GLYBURIDE': 'Glyburide',
  'GLIMEPIRIDE': 'Glimepiride',
  'PIOGLITAZONE': 'Pioglitazone',
  'ACTOS': 'Pioglitazone',
  'ROSIGLITAZONE': 'Rosiglitazone',
  'AVANDIA': 'Rosiglitazone',
  
  // Blood pressure medications
  'LISINOPRIL': 'Lisinopril',
  'ZESTRIL': 'Lisinopril',
  'ENALAPRIL': 'Enalapril',
  'VASOTEC': 'Enalapril',
  'RAMIPRIL': 'Ramipril',
  'ALTACE': 'Ramipril',
  'AMLODIPINE': 'Amlodipine',
  'NORVASC': 'Amlodipine',
  'LOSARTAN': 'Losartan',
  'COZAAR': 'Losartan',
  'VALSARTAN': 'Valsartan',
  'DIOVAN': 'Valsartan',
  'METOPROLOL': 'Metoprolol',
  'LOPRESSOR': 'Metoprolol',
  'ATENOLOL': 'Atenolol',
  'TENORMIN': 'Atenolol',
  
  // Cholesterol medications
  'ATORVASTATIN': 'Atorvastatin',
  'LIPITOR': 'Atorvastatin',
  'SIMVASTATIN': 'Simvastatin',
  'ZOCOR': 'Simvastatin',
  'ROSUVASTATIN': 'Rosuvastatin',
  'CRESTOR': 'Rosuvastatin',
  'PRAVASTATIN': 'Pravastatin',
  'PRAVACHOL': 'Pravastatin',
  
  // Pain medications
  'IBUPROFEN': 'Ibuprofen',
  'ADVIL': 'Ibuprofen',
  'MOTRIN': 'Ibuprofen',
  'ACETAMINOPHEN': 'Acetaminophen',
  'TYLENOL': 'Acetaminophen',
  'PARACETAMOL': 'Acetaminophen',
  'ASPIRIN': 'Aspirin',
  'NAPROXEN': 'Naproxen',
  'ALEVE': 'Naproxen',
  'NAPROSYN': 'Naproxen',
  
  // Antibiotics
  'AMOXICILLIN': 'Amoxicillin',
  'AUGMENTIN': 'Amoxicillin/Clavulanate',
  'AZITHROMYCIN': 'Azithromycin',
  'ZITHROMAX': 'Azithromycin',
  'CEPHALEXIN': 'Cephalexin',
  'KEFLEX': 'Cephalexin',
  'DOXYCYCLINE': 'Doxycycline',
  'VIBRAMYCIN': 'Doxycycline',
  
  // Antidepressants
  'SERTRALINE': 'Sertraline',
  'ZOLOFT': 'Sertraline',
  'FLUOXETINE': 'Fluoxetine',
  'PROZAC': 'Fluoxetine',
  'ESCITALOPRAM': 'Escitalopram',
  'LEXAPRO': 'Escitalopram',
  'VENLAFAXINE': 'Venlafaxine',
  'EFFEXOR': 'Venlafaxine',
  
  // Anxiety medications
  'ALPRAZOLAM': 'Alprazolam',
  'XANAX': 'Alprazolam',
  'LORAZEPAM': 'Lorazepam',
  'ATIVAN': 'Lorazepam',
  'DIAZEPAM': 'Diazepam',
  'VALIUM': 'Diazepam',
  
  // Thyroid medications
  'LEVOTHYROXINE': 'Levothyroxine',
  'SYNTHROID': 'Levothyroxine',
  'LEVOXYL': 'Levothyroxine',
  'LEVOTHROID': 'Levothyroxine',
  
  // Gastrointestinal medications
  'OMEPRAZOLE': 'Omeprazole',
  'PRILOSEC': 'Omeprazole',
  'ESOMEPRAZOLE': 'Esomeprazole',
  'NEXIUM': 'Esomeprazole',
  'LANSOPRAZOLE': 'Lansoprazole',
  'PREVACID': 'Lansoprazole',
  'PANTOPRAZOLE': 'Pantoprazole',
  'PROTONIX': 'Pantoprazole',
  
  // Asthma/COPD medications
  'ALBUTEROL': 'Albuterol',
  'VENTOLIN': 'Albuterol',
  'PROAIR': 'Albuterol',
  'SALBUTAMOL': 'Salbutamol',
  'FLUTICASONE': 'Fluticasone',
  'FLOVENT': 'Fluticasone',
  'BUDESONIDE': 'Budesonide',
  'PULMICORT': 'Budesonide',
  
  // Blood thinners
  'WARFARIN': 'Warfarin',
  'COUMADIN': 'Warfarin',
  'APIXABAN': 'Apixaban',
  'ELIQUIS': 'Apixaban',
  'RIVAROXABAN': 'Rivaroxaban',
  'XARELTO': 'Rivaroxaban',
  'DABIGATRAN': 'Dabigatran',
  'PRADAXA': 'Dabigatran',
  
  // Diuretics
  'FUROSEMIDE': 'Furosemide',
  'LASIX': 'Furosemide',
  'HYDROCHLOROTHIAZIDE': 'Hydrochlorothiazide',
  'HCTZ': 'Hydrochlorothiazide',
  'SPIRONOLACTONE': 'Spironolactone',
  'ALDACTONE': 'Spironolactone'
}

// ============================================================================
// ICD-10 CODE MAPPING
// ============================================================================

export const ICD10_CODES: Record<string, ICD10Code> = {
  // Diabetes mellitus
  'E11': {
    code: 'E11',
    description: 'Type 2 diabetes mellitus',
    category: 'Endocrine disorders'
  },
  'E10': {
    code: 'E10',
    description: 'Type 1 diabetes mellitus',
    category: 'Endocrine disorders'
  },
  'E13': {
    code: 'E13',
    description: 'Other specified diabetes mellitus',
    category: 'Endocrine disorders'
  },
  
  // Hypertension
  'I10': {
    code: 'I10',
    description: 'Essential (primary) hypertension',
    category: 'Cardiovascular diseases'
  },
  'I11': {
    code: 'I11',
    description: 'Hypertensive heart disease',
    category: 'Cardiovascular diseases'
  },
  'I12': {
    code: 'I12',
    description: 'Hypertensive chronic kidney disease',
    category: 'Cardiovascular diseases'
  },
  
  // Heart disease
  'I25': {
    code: 'I25',
    description: 'Chronic ischemic heart disease',
    category: 'Cardiovascular diseases'
  },
  'I50': {
    code: 'I50',
    description: 'Heart failure',
    category: 'Cardiovascular diseases'
  },
  
  // Hyperlipidemia
  'E78': {
    code: 'E78',
    description: 'Disorders of lipoprotein metabolism and other lipidemias',
    category: 'Endocrine disorders'
  },
  
  // Thyroid disorders
  'E03': {
    code: 'E03',
    description: 'Other hypothyroidism',
    category: 'Endocrine disorders'
  },
  'E04': {
    code: 'E04',
    description: 'Other nontoxic goiter',
    category: 'Endocrine disorders'
  },
  'E05': {
    code: 'E05',
    description: 'Thyrotoxicosis [hyperthyroidism]',
    category: 'Endocrine disorders'
  },
  
  // Depression and anxiety
  'F32': {
    code: 'F32',
    description: 'Major depressive disorder, single episode',
    category: 'Mental and behavioral disorders'
  },
  'F33': {
    code: 'F33',
    description: 'Major depressive disorder, recurrent',
    category: 'Mental and behavioral disorders'
  },
  'F41': {
    code: 'F41',
    description: 'Other anxiety disorders',
    category: 'Mental and behavioral disorders'
  },
  
  // Asthma
  'J45': {
    code: 'J45',
    description: 'Asthma',
    category: 'Respiratory diseases'
  },
  
  // COPD
  'J44': {
    code: 'J44',
    description: 'Other chronic obstructive pulmonary disease',
    category: 'Respiratory diseases'
  },
  
  // Gastrointestinal disorders
  'K21': {
    code: 'K21',
    description: 'Gastro-esophageal reflux disease',
    category: 'Digestive system diseases'
  },
  'K29': {
    code: 'K29',
    description: 'Gastritis and duodenitis',
    category: 'Digestive system diseases'
  },
  
  // Pain conditions
  'M79': {
    code: 'M79',
    description: 'Other soft tissue disorders, not elsewhere classified',
    category: 'Musculoskeletal and connective tissue diseases'
  },
  'G89': {
    code: 'G89',
    description: 'Pain, not elsewhere classified',
    category: 'Nervous system diseases'
  }
}

// ============================================================================
// MEDICATION TYPE IDENTIFICATION
// ============================================================================

export const MEDICATION_TYPE_KEYWORDS = {
  tablet: ['tablet', 'tablets', 'tab', 'tabs', 'pill', 'pills', 'oral'],
  capsule: ['capsule', 'capsules', 'cap', 'caps'],
  liquid: ['liquid', 'suspension', 'syrup', 'solution', 'elixir', 'drops'],
  injection: ['injection', 'inject', 'injectable', 'subcutaneous', 'intramuscular', 'intravenous', 'iv', 'sc', 'im'],
  inhaler: ['inhaler', 'inhalation', 'puff', 'puffs', 'nebulizer'],
  cream: ['cream', 'ointment', 'gel', 'lotion', 'topical'],
  patch: ['patch', 'transdermal', 'tds'],
  drops: ['drops', 'eye drops', 'ear drops', 'nasal drops']
}

// ============================================================================
// FREQUENCY MAPPING
// ============================================================================

export const FREQUENCY_MAPPING: Record<string, string> = {
  'once daily': 'daily',
  'once a day': 'daily',
  'daily': 'daily',
  'every day': 'daily',
  'twice daily': 'twice daily',
  'twice a day': 'twice daily',
  '2x daily': 'twice daily',
  'three times daily': 'three times daily',
  'three times a day': 'three times daily',
  '3x daily': 'three times daily',
  'four times daily': 'four times daily',
  'four times a day': 'four times daily',
  '4x daily': 'four times daily',
  'weekly': 'weekly',
  'once a week': 'weekly',
  'monthly': 'monthly',
  'once a month': 'monthly'
}

// ============================================================================
// TIMING MAPPING
// ============================================================================

export const TIMING_MAPPING: Record<string, string> = {
  'morning': 'morning',
  'am': 'morning',
  'breakfast': 'morning',
  'noon': 'noon',
  'midday': 'noon',
  'lunch': 'noon',
  'afternoon': 'afternoon',
  'evening': 'evening',
  'dinner': 'evening',
  'night': 'night',
  'bedtime': 'night',
  'pm': 'night',
  'before meals': 'before meals',
  'after meals': 'after meals',
  'with meals': 'with meals'
}

// ============================================================================
// INTERFACES
// ============================================================================

export interface ParsedPrescription {
  medications: ParsedMedication[]
  prescriptionNumber?: string
  prescribingDoctor?: string
  prescribedDate?: string
  expiryDate?: string
  icd10Codes: ICD10Code[]
  rawText: string
  confidence: number
  warnings: string[]
}

export interface ParsedMedication {
  name: string
  genericName?: string
  strength?: string
  dosage?: string
  frequency?: string
  timing?: string
  quantity?: number
  repeats?: number
  instructions?: string
  medicationType?: string
  category?: string
  confidence: number
  warnings: string[]
}

export interface ParsingOptions {
  expandAbbreviations?: boolean
  validateAgainstDatabase?: boolean
  includeGenericNames?: boolean
  strictMode?: boolean
  language?: 'en' | 'af'
}

// ============================================================================
// MAIN PARSER CLASS
// ============================================================================

export class PrescriptionParser {
  private options: ParsingOptions

  constructor(options: ParsingOptions = {}) {
    this.options = {
      expandAbbreviations: true,
      validateAgainstDatabase: true,
      includeGenericNames: true,
      strictMode: false,
      language: 'en',
      ...options
    }
  }

  /**
   * Parse prescription text and extract structured medication data
   */
  parsePrescription(text: string): ParsedPrescription {
    const normalizedText = this.normalizeText(text)
    const warnings: string[] = []
    let confidence = 1.0

    try {
      // Extract basic prescription information
      const prescriptionNumber = this.extractPrescriptionNumber(normalizedText)
      const prescribingDoctor = this.extractDoctor(normalizedText)
      const prescribedDate = this.extractDate(normalizedText)
      const expiryDate = this.extractExpiryDate(normalizedText)
      const icd10Codes = this.extractICD10Codes(normalizedText)

      // Parse medications
      const medications = this.parseMedications(normalizedText)

      // Calculate overall confidence
      const avgConfidence = medications.reduce((sum, med) => sum + med.confidence, 0) / medications.length
      confidence = Math.min(confidence, avgConfidence)

      // Generate warnings
      if (medications.length === 0) {
        warnings.push('No medications found in prescription text')
        confidence *= 0.5
      }

      if (medications.some(med => med.confidence < 0.7)) {
        warnings.push('Some medications have low confidence scores')
      }

      return {
        medications,
        prescriptionNumber,
        prescribingDoctor,
        prescribedDate,
        expiryDate,
        icd10Codes,
        rawText: text,
        confidence,
        warnings
      }
    } catch (error) {
      console.error('Error parsing prescription:', error)
      return {
        medications: [],
        icd10Codes: [],
        rawText: text,
        confidence: 0,
        warnings: ['Failed to parse prescription text']
      }
    }
  }

  /**
   * Parse individual medications from text
   */
  private parseMedications(text: string): ParsedMedication[] {
    const medications: ParsedMedication[] = []
    const lines = text.split('\n').filter(line => line.trim())

    for (const line of lines) {
      const medication = this.parseMedicationLine(line)
      if (medication) {
        medications.push(medication)
      }
    }

    return medications
  }

  /**
   * Parse a single medication line
   */
  private parseMedicationLine(line: string): ParsedMedication | null {
    const warnings: string[] = []
    let confidence = 1.0

    try {
      // Extract medication name
      const name = this.extractMedicationName(line)
      if (!name) {
        return null
      }

      // Expand abbreviations if enabled
      const expandedName = this.options.expandAbbreviations 
        ? this.expandMedicationAbbreviation(name)
        : name

      // Extract other components
      const strength = this.extractStrength(line)
      const dosage = this.extractDosage(line)
      const frequency = this.extractFrequency(line)
      const timing = this.extractTiming(line)
      const quantity = this.extractQuantity(line)
      const repeats = this.extractRepeats(line)
      const instructions = this.extractInstructions(line)
      const medicationType = this.identifyMedicationType(line)

      // Validate and adjust confidence
      if (!strength && !dosage) {
        warnings.push('No dosage information found')
        confidence *= 0.8
      }

      if (!frequency) {
        warnings.push('No frequency information found')
        confidence *= 0.9
      }

      return {
        name: expandedName,
        strength,
        dosage,
        frequency,
        timing,
        quantity,
        repeats,
        instructions,
        medicationType,
        confidence,
        warnings
      }
    } catch (error) {
      console.error('Error parsing medication line:', error)
      return null
    }
  }

  /**
   * Extract medication name from text
   */
  private extractMedicationName(text: string): string | null {
    const match = text.match(PRESCRIPTION_PATTERNS.MEDICATION_NAME)
    if (match && match[0]) {
      return match[0].trim()
    }
    return null
  }

  /**
   * Expand medication abbreviations
   */
  private expandMedicationAbbreviation(abbreviation: string): string {
    const upperAbbr = abbreviation.toUpperCase()
    return MEDICATION_ABBREVIATIONS[upperAbbr] || abbreviation
  }

  /**
   * Extract strength information
   */
  private extractStrength(text: string): string | undefined {
    const matches = Array.from(text.matchAll(PRESCRIPTION_PATTERNS.DOSAGE))
    if (matches.length > 0) {
      return matches[0][0].trim()
    }
    return undefined
  }

  /**
   * Extract dosage information
   */
  private extractDosage(text: string): string | undefined {
    const strength = this.extractStrength(text)
    if (strength) {
      return strength
    }
    return undefined
  }

  /**
   * Extract frequency information
   */
  private extractFrequency(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.FREQUENCY)
    if (match) {
      const frequency = match[0].toLowerCase()
      return FREQUENCY_MAPPING[frequency] || frequency
    }
    return undefined
  }

  /**
   * Extract timing information
   */
  private extractTiming(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.TIMING)
    if (match) {
      const timing = match[0].toLowerCase()
      return TIMING_MAPPING[timing] || timing
    }
    return undefined
  }

  /**
   * Extract quantity information
   */
  private extractQuantity(text: string): number | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.QUANTITY)
    if (match) {
      return parseInt(match[1], 10)
    }
    return undefined
  }

  /**
   * Extract repeat information
   */
  private extractRepeats(text: string): number | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.REPEATS)
    if (match) {
      return parseInt(match[1], 10)
    }
    return undefined
  }

  /**
   * Extract instructions
   */
  private extractInstructions(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.INSTRUCTIONS)
    if (match) {
      return match[1].trim()
    }
    return undefined
  }

  /**
   * Identify medication type based on keywords
   */
  private identifyMedicationType(text: string): string | undefined {
    const lowerText = text.toLowerCase()
    
    for (const [type, keywords] of Object.entries(MEDICATION_TYPE_KEYWORDS)) {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        return type
      }
    }
    
    return undefined
  }

  /**
   * Extract prescription number
   */
  private extractPrescriptionNumber(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.PRESCRIPTION_NUMBER)
    if (match) {
      return match[1].trim()
    }
    return undefined
  }

  /**
   * Extract doctor information
   */
  private extractDoctor(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.DOCTOR)
    if (match) {
      return match[1].trim()
    }
    return undefined
  }

  /**
   * Extract date information
   */
  private extractDate(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.DATE)
    if (match) {
      return match[1].trim()
    }
    return undefined
  }

  /**
   * Extract expiry date
   */
  private extractExpiryDate(text: string): string | undefined {
    const match = text.match(PRESCRIPTION_PATTERNS.EXPIRY)
    if (match) {
      return match[1].trim()
    }
    return undefined
  }

  /**
   * Extract ICD-10 codes
   */
  private extractICD10Codes(text: string): ICD10Code[] {
    const matches = Array.from(text.matchAll(PRESCRIPTION_PATTERNS.ICD10_CODE))
    const codes: ICD10Code[] = []
    
    for (const match of matches) {
      const code = match[1]
      const icd10Code = ICD10_CODES[code]
      if (icd10Code) {
        codes.push(icd10Code)
      }
    }
    
    return codes
  }

  /**
   * Normalize text for parsing
   */
  private normalizeText(text: string): string {
    return text
      .replace(/\s+/g, ' ')
      .replace(/\n+/g, '\n')
      .trim()
  }

  /**
   * Convert parsed prescription to MedicationFormData
   */
  toMedicationFormData(parsedPrescription: ParsedPrescription): MedicationFormData[] {
    return parsedPrescription.medications.map(med => ({
      name: med.name,
      dosage: med.dosage || '',
      frequency: med.frequency || 'daily',
      time: med.timing || 'morning',
      stock: med.quantity || 0,
      minStock: Math.max(1, Math.floor((med.quantity || 0) * 0.2)),
      instructions: med.instructions || '',
      category: med.medicationType || 'tablet',
      strength: med.strength,
      icd10Code: parsedPrescription.icd10Codes[0]?.code,
      prescriptionNumber: parsedPrescription.prescriptionNumber,
      prescribingDoctor: parsedPrescription.prescribingDoctor,
      expirationDate: parsedPrescription.expiryDate
    }))
  }

  /**
   * Validate parsed data against known medication database
   */
  async validateMedicationData(medications: ParsedMedication[]): Promise<{
    valid: ParsedMedication[]
    invalid: ParsedMedication[]
    suggestions: Record<string, string[]>
  }> {
    const valid: ParsedMedication[] = []
    const invalid: ParsedMedication[] = []
    const suggestions: Record<string, string[]> = {}

    for (const medication of medications) {
      // Basic validation
      if (medication.name && medication.dosage && medication.frequency) {
        valid.push(medication)
      } else {
        invalid.push(medication)
        
        // Generate suggestions
        if (!medication.name) {
          suggestions[medication.name || 'unknown'] = ['Medication name is required']
        }
        if (!medication.dosage) {
          suggestions[medication.name || 'unknown'] = [
            ...(suggestions[medication.name || 'unknown'] || []),
            'Dosage information is required'
          ]
        }
        if (!medication.frequency) {
          suggestions[medication.name || 'unknown'] = [
            ...(suggestions[medication.name || 'unknown'] || []),
            'Frequency information is required'
          ]
        }
      }
    }

    return { valid, invalid, suggestions }
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Create a new prescription parser instance
 */
export function createPrescriptionParser(options?: ParsingOptions): PrescriptionParser {
  return new PrescriptionParser(options)
}

/**
 * Quick parse function for simple use cases
 */
export function parsePrescriptionText(text: string, options?: ParsingOptions): ParsedPrescription {
  const parser = createPrescriptionParser(options)
  return parser.parsePrescription(text)
}

/**
 * Convert prescription text directly to medication form data
 */
export function prescriptionTextToFormData(text: string, options?: ParsingOptions): MedicationFormData[] {
  const parser = createPrescriptionParser(options)
  const parsed = parser.parsePrescription(text)
  return parser.toMedicationFormData(parsed)
}

/**
 * Validate a single medication name against known abbreviations
 */
export function validateMedicationName(name: string): {
  isValid: boolean
  expandedName?: string
  suggestions: string[]
} {
  const upperName = name.toUpperCase()
  const expandedName = MEDICATION_ABBREVIATIONS[upperName]
  
  if (expandedName) {
    return {
      isValid: true,
      expandedName,
      suggestions: []
    }
  }

  // Generate suggestions based on partial matches
  const suggestions = Object.keys(MEDICATION_ABBREVIATIONS)
    .filter(key => key.includes(upperName) || upperName.includes(key))
    .slice(0, 5)
    .map(key => MEDICATION_ABBREVIATIONS[key])

  return {
    isValid: false,
    suggestions
  }
}

/**
 * Extract ICD-10 codes from text
 */
export function extractICD10Codes(text: string): ICD10Code[] {
  const matches = Array.from(text.matchAll(PRESCRIPTION_PATTERNS.ICD10_CODE))
  const codes: ICD10Code[] = []
  
  for (const match of matches) {
    const code = match[1]
    const icd10Code = ICD10_CODES[code]
    if (icd10Code) {
      codes.push(icd10Code)
    }
  }
  
  return codes
}

/**
 * Get medication type from text
 */
export function getMedicationType(text: string): string | undefined {
  const lowerText = text.toLowerCase()
  
  for (const [type, keywords] of Object.entries(MEDICATION_TYPE_KEYWORDS)) {
    if (keywords.some(keyword => lowerText.includes(keyword))) {
      return type
    }
  }
  
  return undefined
}

// ============================================================================
// EXPORT DEFAULT
// ============================================================================

export default PrescriptionParser 