import Tesseract from 'tesseract.js'
import { Medication, BulkMedicationEntry } from '../types/medication'

/**
 * Enhanced OCR Processing Result Interface
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
  imageQuality: ImageQualityAssessment
  prescriptionFormat: PrescriptionFormat
  requiresManualReview: boolean
  batchId?: string
  pageNumber?: number
  totalPages?: number
}

/**
 * Image Quality Assessment Interface
 */
export interface ImageQualityAssessment {
  overallScore: number // 0-1
  resolution: number
  contrast: number
  brightness: number
  blur: number
  noise: number
  skew: number
  isProcessable: boolean
  recommendations: string[]
}

/**
 * Prescription Format Detection
 */
export interface PrescriptionFormat {
  type: 'SA_STANDARD' | 'SA_PRIVATE' | 'INTERNATIONAL' | 'UNKNOWN'
  confidence: number
  features: string[]
  language: 'en' | 'af' | 'mixed'
}

/**
 * OCR Provider Configuration
 */
export interface OCRProviderConfig {
  googleCloudVision?: {
    apiKey: string
    projectId: string
    region: string
  }
  azureComputerVision?: {
    endpoint: string
    apiKey: string
    region: string
  }
  tesseract?: {
    enabled: boolean
    languages: string[]
  }
}

/**
 * Batch Processing Configuration
 */
export interface BatchProcessingConfig {
  maxConcurrent: number
  timeout: number
  retryAttempts: number
  qualityThreshold: number
}

/**
 * Medical Abbreviation Expansion
 */
export interface MedicalAbbreviation {
  abbreviation: string
  fullText: string
  category: 'dosage' | 'frequency' | 'route' | 'timing' | 'instruction'
}

/**
 * Drug Database Cross-Reference Result
 */
export interface DrugValidationResult {
  medicationName: string
  isFound: boolean
  confidence: number
  alternatives: string[]
  warnings: string[]
  interactions: string[]
  contraindications: string[]
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
 * Enhanced OCR Service for Prescription Processing
 */
export class OCRService {
  private static instance: OCRService
  private medicationDatabase: Map<string, MedicationDatabaseEntry> = new Map()
  private processedCache: Map<string, OCRResult> = new Map()
  private tesseractWorker: Tesseract.Worker | null = null
  private isInitialized = false
  
  // Enhanced configuration
  private ocrConfig: OCRProviderConfig = {}
  private batchConfig: BatchProcessingConfig = {
    maxConcurrent: 3,
    timeout: 30000,
    retryAttempts: 2,
    qualityThreshold: 0.6
  }
  
  // Medical abbreviations database
  private medicalAbbreviations: Map<string, MedicalAbbreviation> = new Map()
  
  // Drug validation cache
  private drugValidationCache: Map<string, DrugValidationResult> = new Map()
  
  // Batch processing queue
  private batchQueue: Map<string, Promise<OCRResult>> = new Map()

  // Enhanced medication database (in production, this would come from an API)
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
    { brandName: 'Nurofen', genericName: 'Ibuprofen', strength: '200mg', manufacturer: 'Reckitt Benckiser', category: 'NSAID' },
    // Additional common medications
    { brandName: 'Augmentin', genericName: 'Amoxicillin + Clavulanic acid', strength: '500mg/125mg', manufacturer: 'GSK', category: 'Antibiotic' },
    { brandName: 'Ciprofloxacin', genericName: 'Ciprofloxacin', strength: '500mg', manufacturer: 'Bayer', category: 'Antibiotic' },
    { brandName: 'Omeprazole', genericName: 'Omeprazole', strength: '20mg', manufacturer: 'AstraZeneca', category: 'PPI' },
    { brandName: 'Lansoprazole', genericName: 'Lansoprazole', strength: '30mg', manufacturer: 'Takeda', category: 'PPI' },
    { brandName: 'Metformin', genericName: 'Metformin', strength: '500mg', manufacturer: 'Merck', category: 'Antidiabetic' },
    { brandName: 'Gliclazide', genericName: 'Gliclazide', strength: '80mg', manufacturer: 'Servier', category: 'Antidiabetic' },
    { brandName: 'Amlodipine', genericName: 'Amlodipine', strength: '5mg', manufacturer: 'Pfizer', category: 'CCB' },
    { brandName: 'Losartan', genericName: 'Losartan', strength: '50mg', manufacturer: 'Merck', category: 'ARB' },
    { brandName: 'Simvastatin', genericName: 'Simvastatin', strength: '20mg', manufacturer: 'Merck', category: 'Statin' }
  ]

  // Medical abbreviations database
  private readonly medicalAbbreviationsList: MedicalAbbreviation[] = [
    // Dosage abbreviations
    { abbreviation: 'mg', fullText: 'milligrams', category: 'dosage' },
    { abbreviation: 'ml', fullText: 'milliliters', category: 'dosage' },
    { abbreviation: 'mcg', fullText: 'micrograms', category: 'dosage' },
    { abbreviation: 'g', fullText: 'grams', category: 'dosage' },
    { abbreviation: 'kg', fullText: 'kilograms', category: 'dosage' },
    
    // Frequency abbreviations
    { abbreviation: 'qd', fullText: 'once daily', category: 'frequency' },
    { abbreviation: 'bid', fullText: 'twice daily', category: 'frequency' },
    { abbreviation: 'tid', fullText: 'three times daily', category: 'frequency' },
    { abbreviation: 'qid', fullText: 'four times daily', category: 'frequency' },
    { abbreviation: 'qod', fullText: 'every other day', category: 'frequency' },
    { abbreviation: 'q4h', fullText: 'every 4 hours', category: 'frequency' },
    { abbreviation: 'q6h', fullText: 'every 6 hours', category: 'frequency' },
    { abbreviation: 'q8h', fullText: 'every 8 hours', category: 'frequency' },
    { abbreviation: 'q12h', fullText: 'every 12 hours', category: 'frequency' },
    
    // Route abbreviations
    { abbreviation: 'po', fullText: 'by mouth', category: 'route' },
    { abbreviation: 'im', fullText: 'intramuscular', category: 'route' },
    { abbreviation: 'iv', fullText: 'intravenous', category: 'route' },
    { abbreviation: 'sc', fullText: 'subcutaneous', category: 'route' },
    { abbreviation: 'top', fullText: 'topical', category: 'route' },
    { abbreviation: 'inh', fullText: 'inhalation', category: 'route' },
    
    // Timing abbreviations
    { abbreviation: 'ac', fullText: 'before meals', category: 'timing' },
    { abbreviation: 'pc', fullText: 'after meals', category: 'timing' },
    { abbreviation: 'hs', fullText: 'at bedtime', category: 'timing' },
    { abbreviation: 'am', fullText: 'morning', category: 'timing' },
    { abbreviation: 'pm', fullText: 'evening', category: 'timing' },
    
    // Instruction abbreviations
    { abbreviation: 'prn', fullText: 'as needed', category: 'instruction' },
    { abbreviation: 'stat', fullText: 'immediately', category: 'instruction' },
    { abbreviation: 'sos', fullText: 'if needed', category: 'instruction' },
    { abbreviation: 'ut', fullText: 'as directed', category: 'instruction' },
    { abbreviation: 'w/', fullText: 'with', category: 'instruction' },
    { abbreviation: 'w/o', fullText: 'without', category: 'instruction' }
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
   * Initialize the enhanced OCR service
   */
  public async initialize(config?: OCRProviderConfig): Promise<void> {
    if (this.isInitialized) return

    try {
      // Store configuration
      if (config) {
        this.ocrConfig = config
      }

      // Initialize medical abbreviations
      this.initializeMedicalAbbreviations()

      // Initialize Tesseract if enabled
      if (this.ocrConfig.tesseract?.enabled !== false) {
        this.tesseractWorker = await Tesseract.createWorker({
          logger: m => console.log('Tesseract:', m)
        })

        const languages = this.ocrConfig.tesseract?.languages || ['eng']
        for (const lang of languages) {
          await this.tesseractWorker.loadLanguage(lang)
        }
        await this.tesseractWorker.initialize(languages[0])
        
        // Set OCR parameters for better prescription text recognition
        await this.tesseractWorker.setParameters({
          tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;()-/\\%mgmltabletscapsulesdailyhourstakebeforeaftermorningnoonnightevening',
          tessedit_pageseg_mode: Tesseract.PSM.SINGLE_BLOCK,
          preserve_interword_spaces: '1'
        })
      }

      this.isInitialized = true
      console.log('Enhanced OCR Service initialized successfully')
    } catch (error) {
      console.error('Failed to initialize OCR service:', error)
      throw new Error('OCR initialization failed')
    }
  }

  /**
   * Initialize medical abbreviations database
   */
  private initializeMedicalAbbreviations(): void {
    this.medicalAbbreviationsList.forEach(abbr => {
      this.medicalAbbreviations.set(abbr.abbreviation.toLowerCase(), abbr)
    })
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
   * Enhanced process prescription image with OCR
   */
  public async processPrescription(
    imageFile: File | string,
    options: PreprocessingOptions = {},
    batchId?: string,
    pageNumber?: number
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
          processingTime: Date.now() - startTime,
          batchId,
          pageNumber
        }
      }

      // Assess image quality
      const qualityAssessment = await this.assessImageQuality(imageFile)
      
      // Optimize image if needed
      const optimizedImage = await this.optimizeImage(imageFile, qualityAssessment)
      
      // Detect prescription format
      const formatDetection = await this.detectPrescriptionFormat(optimizedImage)
      
      // Perform OCR with multiple providers
      const ocrResult = await this.performEnhancedOCR(optimizedImage)
      
      // Expand medical abbreviations
      const expandedText = this.expandMedicalAbbreviations(ocrResult.text)
      
      // Parse extracted text
      const parsedResult = this.parsePrescriptionText(expandedText)
      
      // Validate medications against drug database
      const validatedMedications = await this.validateMedications(parsedResult.medications)
      
      // Calculate overall confidence
      const overallConfidence = this.calculateOverallConfidence(ocrResult, parsedResult, qualityAssessment)
      
      // Determine if manual review is required
      const requiresManualReview = this.determineManualReview(overallConfidence, qualityAssessment, validatedMedications)
      
      const result: OCRResult = {
        success: true,
        confidence: overallConfidence,
        text: expandedText,
        medications: validatedMedications,
        prescriptionNumber: parsedResult.prescriptionNumber,
        doctorName: parsedResult.doctorName,
        icd10Codes: parsedResult.icd10Codes,
        rawText: ocrResult.text,
        processingTime: Date.now() - startTime,
        imageQuality: qualityAssessment,
        prescriptionFormat: formatDetection,
        requiresManualReview,
        batchId,
        pageNumber
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
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        imageQuality: {
          overallScore: 0,
          resolution: 0,
          contrast: 0,
          brightness: 0,
          blur: 0,
          noise: 0,
          skew: 0,
          isProcessable: false,
          recommendations: ['Image processing failed']
        },
        prescriptionFormat: {
          type: 'UNKNOWN',
          confidence: 0,
          features: [],
          language: 'en'
        },
        requiresManualReview: true
      }
    }
  }

  /**
   * Assess image quality for OCR processing
   */
  private async assessImageQuality(imageFile: File | string): Promise<ImageQualityAssessment> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        if (!ctx) {
          reject(new Error('Could not get canvas context'))
          return
        }

        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const data = imageData.data

        // Calculate resolution score
        const resolution = Math.min(1, (img.width * img.height) / (1920 * 1080))

        // Calculate contrast
        const contrast = this.calculateContrast(data)

        // Calculate brightness
        const brightness = this.calculateBrightness(data)

        // Calculate blur
        const blur = this.calculateBlur(data, img.width, img.height)

        // Calculate noise
        const noise = this.calculateNoise(data, img.width, img.height)

        // Calculate skew
        const skew = this.calculateSkew(data, img.width, img.height)

        // Calculate overall score
        const overallScore = (resolution * 0.2 + contrast * 0.25 + brightness * 0.2 + 
                             (1 - blur) * 0.2 + (1 - noise) * 0.1 + (1 - skew) * 0.05)

        const recommendations: string[] = []
        if (resolution < 0.5) recommendations.push('Low resolution - consider higher quality image')
        if (contrast < 0.3) recommendations.push('Low contrast - image may be difficult to read')
        if (brightness < 0.3 || brightness > 0.8) recommendations.push('Poor brightness - adjust lighting')
        if (blur > 0.5) recommendations.push('Image is blurry - retake photo')
        if (noise > 0.4) recommendations.push('High noise - improve lighting conditions')
        if (skew > 0.3) recommendations.push('Image is skewed - align camera properly')

        resolve({
          overallScore,
          resolution,
          contrast,
          brightness,
          blur,
          noise,
          skew,
          isProcessable: overallScore > 0.4,
          recommendations
        })
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
   * Optimize image for better OCR results
   */
  private async optimizeImage(
    imageFile: File | string,
    qualityAssessment: ImageQualityAssessment
  ): Promise<HTMLCanvasElement> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        if (!ctx) {
          reject(new Error('Could not get canvas context'))
          return
        }

        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        // Apply optimizations based on quality assessment
        if (qualityAssessment.contrast < 0.5) {
          this.enhanceContrast(ctx, canvas.width, canvas.height)
        }

        if (qualityAssessment.brightness < 0.3 || qualityAssessment.brightness > 0.8) {
          this.adjustBrightness(ctx, canvas.width, canvas.height, qualityAssessment.brightness)
        }

        if (qualityAssessment.skew > 0.2) {
          this.deskewImage(ctx, canvas.width, canvas.height)
        }

        if (qualityAssessment.noise > 0.3) {
          this.reduceNoise(ctx, canvas.width, canvas.height)
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
   * Detect prescription format and language
   */
  private async detectPrescriptionFormat(canvas: HTMLCanvasElement): Promise<PrescriptionFormat> {
    // This would typically use a trained model, but for now we'll use pattern matching
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      return {
        type: 'UNKNOWN',
        confidence: 0,
        features: [],
        language: 'en'
      }
    }

    // Convert canvas to text for analysis (simplified approach)
    const tempResult = await this.performOCR(canvas)
    const text = tempResult.text.toLowerCase()

    const features: string[] = []
    let confidence = 0.5
    let type: PrescriptionFormat['type'] = 'UNKNOWN'
    let language: 'en' | 'af' | 'mixed' = 'en'

    // Check for South African features
    if (text.includes('prescription') || text.includes('voorskrif')) {
      features.push('prescription_header')
      confidence += 0.2
    }

    if (text.includes('dr') || text.includes('doctor') || text.includes('dokter')) {
      features.push('doctor_reference')
      confidence += 0.15
    }

    if (text.includes('patient') || text.includes('pasiënt')) {
      features.push('patient_reference')
      confidence += 0.15
    }

    // Check for Afrikaans
    const afrikaansWords = ['voorskrif', 'pasiënt', 'dokter', 'medikasie', 'medisyne']
    const afrikaansCount = afrikaansWords.filter(word => text.includes(word)).length
    if (afrikaansCount > 0) {
      language = afrikaansCount > 2 ? 'af' : 'mixed'
    }

    // Determine type based on features
    if (features.length >= 3) {
      type = language === 'af' ? 'SA_STANDARD' : 'SA_PRIVATE'
      confidence += 0.2
    }

    return {
      type,
      confidence: Math.min(1, confidence),
      features,
      language
    }
  }

  /**
   * Perform enhanced OCR with multiple providers
   */
  private async performEnhancedOCR(canvas: HTMLCanvasElement): Promise<{ text: string; confidence: number }> {
    const results: Array<{ text: string; confidence: number; provider: string }> = []

    // Try Google Cloud Vision first if configured
    if (this.ocrConfig.googleCloudVision?.apiKey) {
      try {
        const googleResult = await this.performGoogleCloudVisionOCR(canvas)
        results.push({ ...googleResult, provider: 'google' })
      } catch (error) {
        console.warn('Google Cloud Vision failed:', error)
      }
    }

    // Try Azure Computer Vision as fallback
    if (this.ocrConfig.azureComputerVision?.apiKey && results.length === 0) {
      try {
        const azureResult = await this.performAzureComputerVisionOCR(canvas)
        results.push({ ...azureResult, provider: 'azure' })
      } catch (error) {
        console.warn('Azure Computer Vision failed:', error)
      }
    }

    // Use Tesseract as final fallback
    if (results.length === 0 && this.tesseractWorker) {
      try {
        const tesseractResult = await this.performOCR(canvas)
        results.push({ ...tesseractResult, provider: 'tesseract' })
      } catch (error) {
        console.warn('Tesseract failed:', error)
      }
    }

    // Return best result
    if (results.length > 0) {
      const bestResult = results.reduce((best, current) => 
        current.confidence > best.confidence ? current : best
      )
      return { text: bestResult.text, confidence: bestResult.confidence }
    }

    throw new Error('All OCR providers failed')
  }

  /**
   * Perform Google Cloud Vision OCR
   */
  private async performGoogleCloudVisionOCR(canvas: HTMLCanvasElement): Promise<{ text: string; confidence: number }> {
    // This would integrate with Google Cloud Vision API
    // For now, return a placeholder implementation
    throw new Error('Google Cloud Vision API not implemented')
  }

  /**
   * Perform Azure Computer Vision OCR
   */
  private async performAzureComputerVisionOCR(canvas: HTMLCanvasElement): Promise<{ text: string; confidence: number }> {
    // This would integrate with Azure Computer Vision API
    // For now, return a placeholder implementation
    throw new Error('Azure Computer Vision API not implemented')
  }

  /**
   * Expand medical abbreviations in text
   */
  private expandMedicalAbbreviations(text: string): string {
    let expandedText = text

    // Sort abbreviations by length (longest first) to avoid partial matches
    const sortedAbbreviations = Array.from(this.medicalAbbreviations.entries())
      .sort(([a], [b]) => b.length - a.length)

    for (const [abbr, expansion] of sortedAbbreviations) {
      const regex = new RegExp(`\\b${abbr}\\b`, 'gi')
      expandedText = expandedText.replace(regex, expansion.fullText)
    }

    return expandedText
  }

  /**
   * Validate medications against drug database
   */
  private async validateMedications(medications: ExtractedMedication[]): Promise<ExtractedMedication[]> {
    const validatedMedications: ExtractedMedication[] = []

    for (const medication of medications) {
      const validation = await this.validateMedication(medication.name)
      
      if (validation.isFound) {
        validatedMedications.push({
          ...medication,
          confidence: Math.min(1, medication.confidence + 0.2),
          genericName: validation.alternatives[0] || medication.genericName
        })
      } else {
        // Keep medication but mark as unvalidated
        validatedMedications.push({
          ...medication,
          confidence: Math.max(0, medication.confidence - 0.1)
        })
      }
    }

    return validatedMedications
  }

  /**
   * Validate single medication against drug database
   */
  private async validateMedication(medicationName: string): Promise<DrugValidationResult> {
    const cacheKey = medicationName.toLowerCase()
    
    if (this.drugValidationCache.has(cacheKey)) {
      return this.drugValidationCache.get(cacheKey)!
    }

    // Check against local database first
    const entry = this.medicationDatabase.get(cacheKey)
    
    if (entry) {
      const result: DrugValidationResult = {
        medicationName,
        isFound: true,
        confidence: 0.9,
        alternatives: [entry.genericName],
        warnings: [],
        interactions: [],
        contraindications: []
      }
      
      this.drugValidationCache.set(cacheKey, result)
      return result
    }

    // In production, this would call an external API
    const result: DrugValidationResult = {
      medicationName,
      isFound: false,
      confidence: 0.3,
      alternatives: [],
      warnings: ['Medication not found in database'],
      interactions: [],
      contraindications: []
    }

    this.drugValidationCache.set(cacheKey, result)
    return result
  }

  /**
   * Determine if manual review is required
   */
  private determineManualReview(
    confidence: number,
    qualityAssessment: ImageQualityAssessment,
    medications: ExtractedMedication[]
  ): boolean {
    if (confidence < 0.6) return true
    if (qualityAssessment.overallScore < 0.5) return true
    if (medications.some(med => med.confidence < 0.5)) return true
    if (medications.length === 0) return true
    
    return false
  }

  /**
   * Calculate image contrast
   */
  private calculateContrast(data: Uint8ClampedArray): number {
    let min = 255
    let max = 0

    for (let i = 0; i < data.length; i += 4) {
      const gray = (data[i] + data[i + 1] + data[i + 2]) / 3
      min = Math.min(min, gray)
      max = Math.max(max, gray)
    }

    return (max - min) / 255
  }

  /**
   * Calculate image brightness
   */
  private calculateBrightness(data: Uint8ClampedArray): number {
    let sum = 0
    for (let i = 0; i < data.length; i += 4) {
      sum += (data[i] + data[i + 1] + data[i + 2]) / 3
    }
    return sum / (data.length / 4) / 255
  }

  /**
   * Calculate image blur
   */
  private calculateBlur(data: Uint8ClampedArray, width: number, height: number): number {
    // Simplified blur detection using Laplacian variance
    let variance = 0
    let count = 0

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const idx = (y * width + x) * 4
        const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3
        
        const laplacian = Math.abs(
          4 * gray -
          data[((y - 1) * width + x) * 4] -
          data[((y + 1) * width + x) * 4] -
          data[(y * width + x - 1) * 4] -
          data[(y * width + x + 1) * 4]
        )
        
        variance += laplacian
        count++
      }
    }

    return Math.max(0, 1 - (variance / count) / 255)
  }

  /**
   * Calculate image noise
   */
  private calculateNoise(data: Uint8ClampedArray, width: number, height: number): number {
    let noise = 0
    let count = 0

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const idx = (y * width + x) * 4
        const center = (data[idx] + data[idx + 1] + data[idx + 2]) / 3
        
        const neighbors = [
          data[((y - 1) * width + x) * 4],
          data[((y + 1) * width + x) * 4],
          data[(y * width + x - 1) * 4],
          data[(y * width + x + 1) * 4]
        ]
        
        const avgNeighbor = neighbors.reduce((sum, val) => sum + val, 0) / neighbors.length
        noise += Math.abs(center - avgNeighbor)
        count++
      }
    }

    return Math.min(1, (noise / count) / 255)
  }

  /**
   * Calculate image skew
   */
  private calculateSkew(data: Uint8ClampedArray, width: number, height: number): number {
    // Simplified skew detection using Hough transform approximation
    let maxSkew = 0

    for (let y = 0; y < height; y += 10) {
      let leftEdge = 0
      let rightEdge = width - 1

      // Find left edge
      for (let x = 0; x < width; x++) {
        const idx = (y * width + x) * 4
        if ((data[idx] + data[idx + 1] + data[idx + 2]) / 3 < 128) {
          leftEdge = x
          break
        }
      }

      // Find right edge
      for (let x = width - 1; x >= 0; x--) {
        const idx = (y * width + x) * 4
        if ((data[idx] + data[idx + 1] + data[idx + 2]) / 3 < 128) {
          rightEdge = x
          break
        }
      }

      const lineWidth = rightEdge - leftEdge
      if (lineWidth > 0) {
        const skew = Math.abs(y - height / 2) / (height / 2)
        maxSkew = Math.max(maxSkew, skew)
      }
    }

    return maxSkew
  }

  /**
   * Enhance image contrast
   */
  private enhanceContrast(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data

    for (let i = 0; i < data.length; i += 4) {
      data[i] = Math.min(255, Math.max(0, (data[i] - 128) * 1.5 + 128))
      data[i + 1] = Math.min(255, Math.max(0, (data[i + 1] - 128) * 1.5 + 128))
      data[i + 2] = Math.min(255, Math.max(0, (data[i + 2] - 128) * 1.5 + 128))
    }

    ctx.putImageData(imageData, 0, 0)
  }

  /**
   * Adjust image brightness
   */
  private adjustBrightness(ctx: CanvasRenderingContext2D, width: number, height: number, currentBrightness: number): void {
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data

    const targetBrightness = 0.5
    const adjustment = (targetBrightness - currentBrightness) * 255

    for (let i = 0; i < data.length; i += 4) {
      data[i] = Math.min(255, Math.max(0, data[i] + adjustment))
      data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + adjustment))
      data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + adjustment))
    }

    ctx.putImageData(imageData, 0, 0)
  }

  /**
   * Deskew image
   */
  private deskewImage(ctx: CanvasRenderingContext2D, width: number, height: number): void {
    // Simplified deskewing - in production, use more sophisticated algorithms
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data

    // Apply simple rotation correction
    const angle = Math.atan2(height, width) * 0.1
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)

    const newCanvas = document.createElement('canvas')
    const newCtx = newCanvas.getContext('2d')
    if (!newCtx) return

    newCanvas.width = width
    newCanvas.height = height
    newCtx.putImageData(imageData, 0, 0)

    ctx.clearRect(0, 0, width, height)
    ctx.save()
    ctx.translate(width / 2, height / 2)
    ctx.rotate(angle)
    ctx.drawImage(newCanvas, -width / 2, -height / 2)
    ctx.restore()
  }

  /**
   * Reduce image noise
   */
  private reduceNoise(ctx: CanvasRenderingContext2D, width: number, height: number): void {
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
    parsedResult: { medications: ExtractedMedication[] },
    qualityAssessment: ImageQualityAssessment
  ): number {
    const ocrConfidence = ocrResult.confidence / 100 // Normalize to 0-1
    const medicationConfidence = parsedResult.medications.length > 0
      ? parsedResult.medications.reduce((sum, med) => sum + med.confidence, 0) / parsedResult.medications.length
      : 0

    // Weight OCR confidence, medication confidence, and image quality
    return ocrConfidence * 0.5 + medicationConfidence * 0.3 + qualityAssessment.overallScore * 0.2
  }

  /**
   * Process multiple prescription pages in batch
   */
  public async processBatchPrescriptions(
    imageFiles: (File | string)[],
    options: PreprocessingOptions = {}
  ): Promise<OCRResult[]> {
    const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const results: OCRResult[] = []
    
    // Process images with concurrency limit
    const chunks = this.chunkArray(imageFiles, this.batchConfig.maxConcurrent)
    
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i]
      const chunkPromises = chunk.map((imageFile, index) => 
        this.processPrescription(
          imageFile, 
          options, 
          batchId, 
          i * this.batchConfig.maxConcurrent + index + 1
        )
      )
      
      const chunkResults = await Promise.allSettled(chunkPromises)
      
      for (const result of chunkResults) {
        if (result.status === 'fulfilled') {
          results.push({
            ...result.value,
            totalPages: imageFiles.length
          })
        } else {
          // Add error result
          results.push({
            success: false,
            confidence: 0,
            text: '',
            medications: [],
            icd10Codes: [],
            rawText: '',
            processingTime: 0,
            errors: [result.reason?.message || 'Unknown error'],
            imageQuality: {
              overallScore: 0,
              resolution: 0,
              contrast: 0,
              brightness: 0,
              blur: 0,
              noise: 0,
              skew: 0,
              isProcessable: false,
              recommendations: ['Processing failed']
            },
            prescriptionFormat: {
              type: 'UNKNOWN',
              confidence: 0,
              features: [],
              language: 'en'
            },
            requiresManualReview: true,
            batchId,
            totalPages: imageFiles.length
          })
        }
      }
    }
    
    return results
  }

  /**
   * Split array into chunks for batch processing
   */
  private chunkArray<T>(array: T[], chunkSize: number): T[][] {
    const chunks: T[][] = []
    for (let i = 0; i < array.length; i += chunkSize) {
      chunks.push(array.slice(i, i + chunkSize))
    }
    return chunks
  }

  /**
   * Configure batch processing settings
   */
  public configureBatchProcessing(config: Partial<BatchProcessingConfig>): void {
    this.batchConfig = { ...this.batchConfig, ...config }
  }

  /**
   * Get batch processing statistics
   */
  public getBatchStats(): {
    queueSize: number
    config: BatchProcessingConfig
    cacheStats: { size: number; entries: string[] }
  } {
    return {
      queueSize: this.batchQueue.size,
      config: this.batchConfig,
      cacheStats: this.getCacheStats()
    }
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
   * Enhanced validate OCR result with confidence-based validation
   */
  public validateResult(result: OCRResult): {
    isValid: boolean
    suggestions: string[]
    requiresManualEntry: boolean
    qualityIssues: string[]
    formatIssues: string[]
  } {
    const suggestions: string[] = []
    const qualityIssues: string[] = []
    const formatIssues: string[] = []
    let requiresManualEntry = false

    // Check overall confidence
    if (result.confidence < 0.6) {
      suggestions.push('OCR confidence is low. Consider manual entry for better accuracy.')
      requiresManualEntry = true
    }

    // Check image quality
    if (result.imageQuality.overallScore < 0.5) {
      qualityIssues.push('Image quality is poor and may affect OCR accuracy.')
      requiresManualEntry = true
    }

    if (result.imageQuality.contrast < 0.3) {
      qualityIssues.push('Low contrast detected - consider retaking photo with better lighting.')
    }

    if (result.imageQuality.blur > 0.5) {
      qualityIssues.push('Image is blurry - retake photo with steady hands.')
    }

    // Check prescription format
    if (result.prescriptionFormat.confidence < 0.5) {
      formatIssues.push('Prescription format not clearly identified.')
    }

    if (result.prescriptionFormat.type === 'UNKNOWN') {
      formatIssues.push('Unable to determine prescription format.')
    }

    // Check medications
    if (result.medications.length === 0) {
      suggestions.push('No medications detected. Please check the image quality or enter manually.')
      requiresManualEntry = true
    }

    if (result.medications.some(med => med.confidence < 0.5)) {
      suggestions.push('Some medications have low confidence scores. Review and correct as needed.')
    }

    // Check for unvalidated medications
    const unvalidatedMedications = result.medications.filter(med => 
      !this.medicationDatabase.has(med.name.toLowerCase())
    )
    if (unvalidatedMedications.length > 0) {
      suggestions.push(`${unvalidatedMedications.length} medication(s) not found in database. Please verify spelling.`)
    }

    // Check required fields
    if (!result.prescriptionNumber) {
      suggestions.push('Prescription number not detected. Please enter manually if required.')
    }

    if (!result.doctorName) {
      suggestions.push('Doctor name not detected. Please enter manually if required.')
    }

    // Add image quality recommendations
    if (result.imageQuality.recommendations.length > 0) {
      suggestions.push(...result.imageQuality.recommendations)
    }

    return {
      isValid: result.success && result.confidence >= 0.4 && result.imageQuality.overallScore >= 0.4,
      suggestions,
      requiresManualEntry,
      qualityIssues,
      formatIssues
    }
  }

  /**
   * Get detailed medication validation report
   */
  public async getMedicationValidationReport(medications: ExtractedMedication[]): Promise<{
    validated: ExtractedMedication[]
    unvalidated: ExtractedMedication[]
    warnings: string[]
    interactions: string[]
  }> {
    const validated: ExtractedMedication[] = []
    const unvalidated: ExtractedMedication[] = []
    const warnings: string[] = []
    const interactions: string[] = []

    for (const medication of medications) {
      const validation = await this.validateMedication(medication.name)
      
      if (validation.isFound) {
        validated.push(medication)
        warnings.push(...validation.warnings)
        interactions.push(...validation.interactions)
      } else {
        unvalidated.push(medication)
        warnings.push(`Medication "${medication.name}" not found in database`)
      }
    }

    return {
      validated,
      unvalidated,
      warnings,
      interactions
    }
  }

  /**
   * Clear all caches
   */
  public clearAllCaches(): void {
    this.processedCache.clear()
    this.drugValidationCache.clear()
    this.batchQueue.clear()
  }

  /**
   * Get comprehensive service statistics
   */
  public getServiceStats(): {
    cacheStats: { size: number; entries: string[] }
    batchStats: { queueSize: number; config: BatchProcessingConfig }
    validationStats: { validated: number; unvalidated: number }
    qualityStats: { averageScore: number; recommendations: string[] }
  } {
    const cacheStats = this.getCacheStats()
    const batchStats = this.getBatchStats()
    
    // Calculate validation stats
    let validated = 0
    let unvalidated = 0
    for (const entry of this.drugValidationCache.values()) {
      if (entry.isFound) validated++
      else unvalidated++
    }

    // Calculate quality stats
    const qualityScores: number[] = []
    const allRecommendations: string[] = []
    for (const result of this.processedCache.values()) {
      qualityScores.push(result.imageQuality.overallScore)
      allRecommendations.push(...result.imageQuality.recommendations)
    }

    const averageScore = qualityScores.length > 0 
      ? qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length 
      : 0

    return {
      cacheStats,
      batchStats,
      validationStats: { validated, unvalidated },
      qualityStats: {
        averageScore,
        recommendations: [...new Set(allRecommendations)]
      }
    }
  }
}

// Export singleton instance
export const ocrService = OCRService.getInstance() 