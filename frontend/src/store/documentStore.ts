import { create } from 'zustand'
import { Document, Summary, ProcessingStatus } from '@/types'

interface DocumentStore {
  documents: Document[]
  currentDocument: Document | null
  currentSummary: Summary | null
  processingStatus: ProcessingStatus | null
  isLoading: boolean
  error: string | null

  // Actions
  setDocuments: (documents: Document[]) => void
  addDocument: (document: Document) => void
  updateDocument: (id: string, updates: Partial<Document>) => void
  removeDocument: (id: string) => void
  setCurrentDocument: (document: Document | null) => void
  setCurrentSummary: (summary: Summary | null) => void
  setProcessingStatus: (status: ProcessingStatus | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  documents: [],
  currentDocument: null,
  currentSummary: null,
  processingStatus: null,
  isLoading: false,
  error: null,

  setDocuments: (documents) => set({ documents }),

  addDocument: (document) => set((state) => ({
    documents: [document, ...state.documents]
  })),

  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map(doc => 
      doc.id === id ? { ...doc, ...updates } : doc
    ),
    currentDocument: state.currentDocument?.id === id 
      ? { ...state.currentDocument, ...updates }
      : state.currentDocument
  })),

  removeDocument: (id) => set((state) => ({
    documents: state.documents.filter(doc => doc.id !== id),
    currentDocument: state.currentDocument?.id === id ? null : state.currentDocument,
    currentSummary: state.currentSummary?.documentId === id ? null : state.currentSummary
  })),

  setCurrentDocument: (document) => set({ currentDocument: document }),

  setCurrentSummary: (summary) => set({ currentSummary: summary }),

  setProcessingStatus: (status) => set({ processingStatus: status }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),
}))

// Selectors
export const useDocuments = () => useDocumentStore(state => state.documents)
export const useCurrentDocument = () => useDocumentStore(state => state.currentDocument)
export const useCurrentSummary = () => useDocumentStore(state => state.currentSummary)
export const useProcessingStatus = () => useDocumentStore(state => state.processingStatus)
export const useDocumentLoading = () => useDocumentStore(state => state.isLoading)
export const useDocumentError = () => useDocumentStore(state => state.error)
