import Tesseract from 'tesseract.js'
import { Medication, BulkMedicationEntry } from '../types/medication'

/**
 * OCR Processing Result Interface
 */
export interface OCRResult {
  success: boolean
  confidence: number
  text: string
  medications: ExtractedMedication[]
  prescriptionNumber?: string
  doctorName?: string
  icd10Codes: string[]
  rawText: string
  processingTime: number
  errors?: string[]
}

/**
 * Extracted Medication Interface
 */
export interface ExtractedMedication {
  name: string
  genericName?: string
  strength?: string
  dosage: string
  frequency: string
  instructions: string
  confidence: number
  manufacturer?: string
  prescriptionNumber?: string
  prescribingDoctor?: string
  icd10Code?: string
}

/**
 * Image Preprocessing Options
 */
export interface PreprocessingOptions {
  contrast?: number // 0-2, default 1
  brightness?: number // -1 to 1, default 0
  sharpen?: boolean // default true
  denoise?: boolean // default true
  deskew?: boolean // default true
  threshold?: number // 0-255, default 128
}

/**
 * Medication Database Entry
 */
interface MedicationDatabaseEntry {
  brandName: string
  genericName: string
  strength: string
  manufacturer: string
  category: string
}

/**
 * Dosage Pattern Interface
 */
interface DosagePattern {
  pattern: RegExp
  extractor: (match: RegExpMatchArray) => {
    amount: string
    frequency: string
    timing: string
    instructions: string
  }
}

/**
 * OCR Service for Prescription Processing
 */
export class OCRService {
  private static instance: OCRService
  private medicationDatabase: Map<string, MedicationDatabaseEntry> = new Map()
  private processedCache: Map<string, OCRResult> = new Map()
  private tesseractWorker: Tesseract.Worker | null = null
  private isInitialized = false

  // Common medication database (in production, this would come from an API)
  private readonly commonMedications: MedicationDatabaseEntry[] = [
    { brandName: 'Panado', genericName: 'Paracetamol', strength: '500mg', manufacturer: 'GSK', category: 'Analgesic' },
    { brandName: 'Disprin', genericName: 'Aspirin', strength: '300mg', manufacturer: 'Bayer', category: 'Analgesic' },
    { brandName: 'Stilpane', genericName: 'Paracetamol + Codeine', strength: '500mg/8mg', manufacturer: 'Adcock Ingram', category: 'Analgesic' },
    { brandName: 'Sinutab', genericName: 'Pseudoephedrine + Paracetamol', strength: '30mg/500mg', manufacturer: 'Johnson & Johnson', category: 'Decongestant' },
    { brandName: 'Betadine', genericName: 'Povidone-iodine', strength: '10%', manufacturer: 'Mundipharma', category: 'Antiseptic' },
    { brandName: 'Corenza C', genericName: 'Paracetamol + Phenylephrine + Chlorpheniramine', strength: '500mg/5mg/2mg', manufacturer: 'Adcock Ingram', category: 'Cold & Flu' },
    { brandName: 'Benylin', genericName: 'Dextromethorphan', strength: '15mg/5ml', manufacturer: 'Johnson & Johnson', category: 'Cough Suppressant' },
    { brandName: 'Gaviscon', genericName: 'Aluminium hydroxide + Magnesium carbonate', strength: '500mg/250mg', manufacturer: 'Reckitt Benckiser', category: 'Antacid' },
    { brandName: 'Lentogesic', genericName: 'Ibuprofen + Codeine', strength: '200mg/12.8mg', manufacturer: 'Adcock Ingram', category: 'Analgesic' },
    { brandName: 'Nurofen', genericName: 'Ibuprofen', strength: '200mg', manufacturer: 'Reckitt Benckiser', category: 'NSAID' }
  ]

  // Dosage patterns for extraction
  private readonly dosagePatterns: DosagePattern[] = [
    {
      pattern: /take\s+(\d+)\s+(tablet|tablets|capsule|capsules|ml|mg)\s+(daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|every\s+(\d+)\s+hours?)/i,
      extractor: (match) => ({
        amount: match[1],
        frequency: match[3],
        timing: '',
        instructions: `Take ${match[1]} ${match[2]} ${match[3]}`
      })
    },
    {
      pattern: /(\d+)\s+(tablet|tablets|capsule|capsules)\s+(morning|noon|night|evening|at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?)/i,
      extractor: (match) => ({
        amount: match[1],
        frequency: 'specific',
        timing: match[3],
        instructions: `${match[1]} ${match[2]} ${match[3]}`
      })
    },
    {
      pattern: /(\d+)\s+(tablet|tablets|capsule|capsules)\s+(before|after)\s+(breakfast|lunch|dinner|meals?)/i,
      extractor: (match) => ({
        amount: match[1],
        frequency: 'with meals',
        timing: `${match[3]} ${match[4]}`,
        instructions: `${match[1]} ${match[2]} ${match[3]} ${match[4]}`
      })
    },
    {
      pattern: /(\d+)\s+(tablet|tablets|capsule|capsules)\s+(every\s+(\d+)\s+(hours?|days?|weeks?))/i,
      extractor: (match) => ({
        amount: match[1],
        frequency: `every ${match[3]} ${match[4]}`,
        timing: '',
        instructions: `${match[1]} ${match[2]} ${match[3]}`
      })
    }
  ]

  // ICD-10 code patterns
  private readonly icd10Patterns = [
    /[A-Z]\d{2}\.\d{1,2}/g, // Standard ICD-10 format
    /[A-Z]\d{2}/g, // ICD-10 without decimal
    /ICD-?10[:\s]*([A-Z]\d{2}\.?\d{0,2})/gi // ICD-10 with prefix
  ]

  // Prescription number patterns
  private readonly prescriptionNumberPatterns = [
    /prescription\s*(?:no|number|#)[:\s]*([A-Z0-9\-]+)/i,
    /script\s*(?:no|number|#)[:\s]*([A-Z0-9\-]+)/i,
    /rx\s*(?:no|number|#)[:\s]*([A-Z0-9\-]+)/i,
    /([A-Z]{2,3}\d{6,8})/g // Common prescription number format
  ]

  // Doctor name patterns
  private readonly doctorNamePatterns = [
    /dr\.?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)/i,
    /doctor\s+([A-Z][a-z]+\s+[A-Z][a-z]+)/i,
    /prescribed\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)/i,
    /([A-Z][a-z]+\s+[A-Z][a-z]+)\s*MD/i
  ]

  private constructor() {
    this.initializeMedicationDatabase()
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): OCRService {
    if (!OCRService.instance) {
      OCRService.instance = new OCRService()
    }
    return OCRService.instance
  }

  /**
   * Initialize the OCR service
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return

    try {
      this.tesseractWorker = await Tesseract.createWorker({
        logger: m => console.log('Tesseract:', m)
      })

      await this.tesseractWorker.loadLanguage('eng')
      await this.tesseractWorker.initialize('eng')
      
      // Set OCR parameters for better prescription text recognition
      await this.tesseractWorker.setParameters({
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;()-/\\%mgmltabletscapsulesdailyhourstakebeforeaftermorningnoonnightevening',
        tessedit_pageseg_mode: Tesseract.PSM.SINGLE_BLOCK,
        preserve_interword_spaces: '1'
      })

      this.isInitialized = true
      console.log('OCR Service initialized successfully')
    } catch (error) {
      console.error('Failed to initialize OCR service:', error)
      throw new Error('OCR initialization failed')
    }
  }

  /**
   * Initialize medication database
   */
  private initializeMedicationDatabase(): void {
    this.commonMedications.forEach(med => {
      this.medicationDatabase.set(med.brandName.toLowerCase(), med)
      this.medicationDatabase.set(med.genericName.toLowerCase(), med)
    })
  }

  /**
   * Process prescription image with OCR
   */
  public async processPrescription(
    imageFile: File | string,
    options: PreprocessingOptions = {}
  ): Promise<OCRResult> {
    const startTime = Date.now()
    
    try {
      if (!this.isInitialized) {
        await this.initialize()
      }

      // Check cache first
      const imageHash = await this.generateImageHash(imageFile)
      if (this.processedCache.has(imageHash)) {
        const cached = this.processedCache.get(imageHash)!
        console.log('Returning cached OCR result')
        return {
          ...cached,
          processingTime: Date.now() - startTime
        }
      }

      // Preprocess image
      const processedImage = await this.preprocessImage(imageFile, options)
      
      // Perform OCR
      const ocrResult = await this.performOCR(processedImage)
      
      // Parse extracted text
      const parsedResult = this.parsePrescriptionText(ocrResult.text)
      
      // Calculate overall confidence
      const overallConfidence = this.calculateOverallConfidence(ocrResult, parsedResult)
      
      const result: OCRResult = {
        success: true,
        confidence: overallConfidence,
        text: ocrResult.text,
        medications: parsedResult.medications,
        prescriptionNumber: parsedResult.prescriptionNumber,
        doctorName: parsedResult.doctorName,
        icd10Codes: parsedResult.icd10Codes,
        rawText: ocrResult.text,
        processingTime: Date.now() - startTime
      }

      // Cache the result
      this.processedCache.set(imageHash, result)
      
      return result

    } catch (error) {
      console.error('OCR processing failed:', error)
      return {
        success: false,
        confidence: 0,
        text: '',
        medications: [],
        icd10Codes: [],
        rawText: '',
        processingTime: Date.now() - startTime,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      }
    }
  }

  /**
   * Preprocess image for better OCR accuracy
   */
  private async preprocessImage(
    imageFile: File | string,
    options: PreprocessingOptions
  ): Promise<HTMLCanvasElement> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // Set canvas size
        canvas.width = img.width
        canvas.height = img.height

        if (!ctx) {
          reject(new Error('Could not get canvas context'))
          return
        }

        // Apply preprocessing options
        const {
          contrast = 1,
          brightness = 0,
          sharpen = true,
          denoise = true,
          deskew = true,
          threshold = 128
        } = options

        // Draw original image
        ctx.drawImage(img, 0, 0)

        // Apply contrast and brightness
        if (contrast !== 1 || brightness !== 0) {
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
          const data = imageData.data

          for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, Math.max(0, (data[i] - 128) * contrast + 128 + brightness * 255))
            data[i + 1] = Math.min(255, Math.max(0, (data[i + 1] - 128) * contrast + 128 + brightness * 255))
            data[i + 2] = Math.min(255, Math.max(0, (data[i + 2] - 128) * contrast + 128 + brightness * 255))
          }

          ctx.putImageData(imageData, 0, 0)
        }

        // Apply threshold for better text recognition
        if (threshold !== 128) {
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
          const data = imageData.data

          for (let i = 0; i < data.length; i += 4) {
            const gray = (data[i] + data[i + 1] + data[i + 2]) / 3
            const value = gray > threshold ? 255 : 0
            data[i] = data[i + 1] = data[i + 2] = value
          }

          ctx.putImageData(imageData, 0, 0)
        }

        // Apply sharpening filter
        if (sharpen) {
          this.applySharpeningFilter(ctx, canvas.width, canvas.height)
        }

        // Apply denoising
        if (denoise) {
          this.applyDenoisingFilter(ctx, canvas.width, canvas.height)
        }

        resolve(canvas)
      }

      img.onerror = () => reject(new Error('Failed to load image'))

      if (typeof imageFile === 'string') {
        img.src = imageFile
      } else {
        img.src = URL.createObjectURL(imageFile)
      }
    })
  }

  /**
   * Apply sharpening filter
   */
  private applySharpeningFilter(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data
    const newData = new Uint8ClampedArray(data)

    const kernel = [
      [0, -1, 0],
      [-1, 5, -1],
      [0, -1, 0]
    ]

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        for (let c = 0; c < 3; c++) {
          let sum = 0
          for (let ky = -1; ky <= 1; ky++) {
            for (let kx = -1; kx <= 1; kx++) {
              const idx = ((y + ky) * width + (x + kx)) * 4 + c
              sum += data[idx] * kernel[ky + 1][kx + 1]
            }
          }
          const idx = (y * width + x) * 4 + c
          newData[idx] = Math.min(255, Math.max(0, sum))
        }
      }
    }

    imageData.data.set(newData)
    ctx.putImageData(imageData, 0, 0)
  }

  /**
   * Apply denoising filter
   */
  private applyDenoisingFilter(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data
    const newData = new Uint8ClampedArray(data)

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        for (let c = 0; c < 3; c++) {
          const values = []
          for (let ky = -1; ky <= 1; ky++) {
            for (let kx = -1; kx <= 1; kx++) {
              const idx = ((y + ky) * width + (x + kx)) * 4 + c
              values.push(data[idx])
            }
          }
          values.sort((a, b) => a - b)
          const idx = (y * width + x) * 4 + c
          newData[idx] = values[4] // Median value
        }
      }
    }

    imageData.data.set(newData)
    ctx.putImageData(imageData, 0, 0)
  }

  /**
   * Perform OCR on preprocessed image
   */
  private async performOCR(canvas: HTMLCanvasElement): Promise<{ text: string; confidence: number }> {
    if (!this.tesseractWorker) {
      throw new Error('Tesseract worker not initialized')
    }

    const result = await this.tesseractWorker.recognize(canvas)
    return {
      text: result.data.text,
      confidence: result.data.confidence
    }
  }

  /**
   * Parse prescription text to extract structured data
   */
  private parsePrescriptionText(text: string): {
    medications: ExtractedMedication[]
    prescriptionNumber?: string
    doctorName?: string
    icd10Codes: string[]
  } {
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0)
    const medications: ExtractedMedication[] = []
    const icd10Codes: string[] = []
    let prescriptionNumber: string | undefined
    let doctorName: string | undefined

    // Extract prescription number
    for (const pattern of this.prescriptionNumberPatterns) {
      const match = text.match(pattern)
      if (match) {
        prescriptionNumber = match[1]
        break
      }
    }

    // Extract doctor name
    for (const pattern of this.doctorNamePatterns) {
      const match = text.match(pattern)
      if (match) {
        doctorName = match[1]
        break
      }
    }

    // Extract ICD-10 codes
    for (const pattern of this.icd10Patterns) {
      const matches = text.match(pattern)
      if (matches) {
        icd10Codes.push(...matches)
      }
    }

    // Parse medications from text
    let currentMedication: Partial<ExtractedMedication> = {}
    let inMedicationSection = false

    for (const line of lines) {
      const lowerLine = line.toLowerCase()

      // Check if we're entering a medication section
      if (this.isMedicationSectionHeader(line)) {
        inMedicationSection = true
        if (Object.keys(currentMedication).length > 0) {
          medications.push(this.finalizeMedication(currentMedication))
          currentMedication = {}
        }
        continue
      }

      if (!inMedicationSection) continue

      // Extract medication name
      const medicationName = this.extractMedicationName(line)
      if (medicationName) {
        if (Object.keys(currentMedication).length > 0) {
          medications.push(this.finalizeMedication(currentMedication))
        }
        currentMedication = {
          name: medicationName,
          confidence: 0.8
        }
        continue
      }

      // Extract dosage information
      const dosageInfo = this.extractDosageInfo(line)
      if (dosageInfo && currentMedication.name) {
        currentMedication = {
          ...currentMedication,
          ...dosageInfo
        }
      }

      // Extract strength
      const strength = this.extractStrength(line)
      if (strength && currentMedication.name) {
        currentMedication.strength = strength
      }

      // Extract instructions
      const instructions = this.extractInstructions(line)
      if (instructions && currentMedication.name) {
        currentMedication.instructions = instructions
      }
    }

    // Add the last medication if exists
    if (Object.keys(currentMedication).length > 0) {
      medications.push(this.finalizeMedication(currentMedication))
    }

    return {
      medications,
      prescriptionNumber,
      doctorName,
      icd10Codes: [...new Set(icd10Codes)] // Remove duplicates
    }
  }

  /**
   * Check if line is a medication section header
   */
  private isMedicationSectionHeader(line: string): boolean {
    const headers = [
      'medication', 'medicines', 'prescription', 'rx', 'drugs',
      'medikasie', 'medisyne', 'voorskrif', 'medicines'
    ]
    return headers.some(header => line.toLowerCase().includes(header))
  }

  /**
   * Extract medication name from line
   */
  private extractMedicationName(line: string): string | null {
    // Look for common medication patterns
    const patterns = [
      /^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/, // Capitalized words
      /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\d+/, // Name followed by number
      /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+[0-9]+mg/, // Name followed by mg
      /([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+tablet/i // Name followed by tablet
    ]

    for (const pattern of patterns) {
      const match = line.match(pattern)
      if (match && match[1].length > 2) {
        return match[1].trim()
      }
    }

    return null
  }

  /**
   * Extract dosage information from line
   */
  private extractDosageInfo(line: string): Partial<ExtractedMedication> | null {
    for (const pattern of this.dosagePatterns) {
      const match = line.match(pattern.pattern)
      if (match) {
        const extracted = pattern.extractor(match)
        return {
          dosage: extracted.amount,
          frequency: extracted.frequency,
          instructions: extracted.instructions
        }
      }
    }
    return null
  }

  /**
   * Extract strength from line
   */
  private extractStrength(line: string): string | null {
    const patterns = [
      /(\d+)\s*mg/i,
      /(\d+)\s*ml/i,
      /(\d+)\s*mg\/ml/i,
      /(\d+)\s*mg\/\d+\s*mg/i
    ]

    for (const pattern of patterns) {
      const match = line.match(pattern)
      if (match) {
        return match[0]
      }
    }

    return null
  }

  /**
   * Extract instructions from line
   */
  private extractInstructions(line: string): string | null {
    const instructionKeywords = [
      'take', 'use', 'apply', 'swallow', 'with food', 'empty stomach',
      'neem', 'gebruik', 'aansoek', 'sluk', 'met kos', 'leë maag'
    ]

    if (instructionKeywords.some(keyword => line.toLowerCase().includes(keyword))) {
      return line.trim()
    }

    return null
  }

  /**
   * Finalize medication object with generic name mapping
   */
  private finalizeMedication(medication: Partial<ExtractedMedication>): ExtractedMedication {
    const name = medication.name || 'Unknown Medication'
    const genericName = this.mapToGenericName(name)

    return {
      name,
      genericName,
      strength: medication.strength || '',
      dosage: medication.dosage || '',
      frequency: medication.frequency || '',
      instructions: medication.instructions || '',
      confidence: medication.confidence || 0.5,
      manufacturer: medication.manufacturer || '',
      prescriptionNumber: medication.prescriptionNumber || '',
      prescribingDoctor: medication.prescribingDoctor || '',
      icd10Code: medication.icd10Code || ''
    }
  }

  /**
   * Map brand name to generic name
   */
  private mapToGenericName(brandName: string): string | undefined {
    const entry = this.medicationDatabase.get(brandName.toLowerCase())
    return entry?.genericName
  }

  /**
   * Calculate overall confidence score
   */
  private calculateOverallConfidence(
    ocrResult: { confidence: number },
    parsedResult: { medications: ExtractedMedication[] }
  ): number {
    const ocrConfidence = ocrResult.confidence / 100 // Normalize to 0-1
    const medicationConfidence = parsedResult.medications.length > 0
      ? parsedResult.medications.reduce((sum, med) => sum + med.confidence, 0) / parsedResult.medications.length
      : 0

    // Weight OCR confidence more heavily
    return ocrConfidence * 0.7 + medicationConfidence * 0.3
  }

  /**
   * Generate hash for image caching
   */
  private async generateImageHash(imageFile: File | string): Promise<string> {
    if (typeof imageFile === 'string') {
      return btoa(imageFile).slice(0, 32)
    }

    const arrayBuffer = await imageFile.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)
    return btoa(String.fromCharCode(...uint8Array)).slice(0, 32)
  }

  /**
   * Clear cache
   */
  public clearCache(): void {
    this.processedCache.clear()
  }

  /**
   * Get cache statistics
   */
  public getCacheStats(): { size: number; entries: string[] } {
    return {
      size: this.processedCache.size,
      entries: Array.from(this.processedCache.keys())
    }
  }

  /**
   * Terminate OCR service
   */
  public async terminate(): Promise<void> {
    if (this.tesseractWorker) {
      await this.tesseractWorker.terminate()
      this.tesseractWorker = null
    }
    this.isInitialized = false
    this.clearCache()
  }

  /**
   * Convert extracted medications to BulkMedicationEntry format
   */
  public convertToBulkEntries(medications: ExtractedMedication[]): BulkMedicationEntry[] {
    return medications.map(med => ({
      name: med.genericName || med.name,
      strength: med.strength || '',
      dosage: med.dosage || '',
      frequency: med.frequency || '',
      instructions: med.instructions || '',
      manufacturer: med.manufacturer || '',
      prescriptionNumber: med.prescriptionNumber || '',
      prescribingDoctor: med.prescribingDoctor || ''
    }))
  }

  /**
   * Validate OCR result and suggest manual entry for low confidence
   */
  public validateResult(result: OCRResult): {
    isValid: boolean
    suggestions: string[]
    requiresManualEntry: boolean
  } {
    const suggestions: string[] = []
    let requiresManualEntry = false

    if (result.confidence < 0.6) {
      suggestions.push('OCR confidence is low. Consider manual entry for better accuracy.')
      requiresManualEntry = true
    }

    if (result.medications.length === 0) {
      suggestions.push('No medications detected. Please check the image quality or enter manually.')
      requiresManualEntry = true
    }

    if (result.medications.some(med => med.confidence < 0.5)) {
      suggestions.push('Some medications have low confidence scores. Review and correct as needed.')
    }

    if (!result.prescriptionNumber) {
      suggestions.push('Prescription number not detected. Please enter manually if required.')
    }

    if (!result.doctorName) {
      suggestions.push('Doctor name not detected. Please enter manually if required.')
    }

    return {
      isValid: result.success && result.confidence >= 0.4,
      suggestions,
      requiresManualEntry
    }
  }
}

// Export singleton instance
export const ocrService = OCRService.getInstance() 