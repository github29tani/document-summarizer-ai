export interface Document {
  id: string
  filename: string
  originalName: string
  fileSize: number
  uploadedAt: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  summary?: Summary
  highlights?: Highlight[]
  pageCount?: number
  textContent?: string
}

export interface Summary {
  id: string
  documentId: string
  content: string
  keyPoints: string[]
  createdAt: string
  processingTime: number
}

export interface Highlight {
  id: string
  documentId: string
  pageNumber: number
  x: number
  y: number
  width: number
  height: number
  text: string
  type: 'key-point' | 'important' | 'definition'
  confidence: number
}

export interface UploadProgress {
  documentId: string
  progress: number
  status: string
}

export interface ProcessingStatus {
  documentId: string
  stage: 'text-extraction' | 'summarization' | 'highlighting' | 'completed'
  progress: number
  message: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}
