import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Document, Page, pdfjs } from 'react-pdf'
import { 
  ArrowLeft, 
  ZoomIn, 
  ZoomOut, 
  Download, 
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { motion } from 'framer-motion'
import { useDocumentStore } from '@/store/documentStore'
import { documentApi, summaryApi } from '@/lib/api'
import toast from 'react-hot-toast'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

export function DocumentViewer() {
  const { id } = useParams<{ id: string }>()
  const { 
    currentDocument, 
    currentSummary,
    setCurrentDocument, 
    setCurrentSummary,
    isLoading,
    setLoading,
    error,
    setError
  } = useDocumentStore()

  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.2)
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false)

  useEffect(() => {
    if (id) {
      loadDocument(id)
    }
  }, [id])

  const loadDocument = async (documentId: string) => {
    setLoading(true)
    setError(null)

    try {
      const document = await documentApi.getDocument(documentId)
      setCurrentDocument(document)

      // Try to load existing summary
      if (document.summary) {
        setCurrentSummary(document.summary)
      } else {
        try {
          const summary = await summaryApi.getSummary(documentId)
          setCurrentSummary(summary)
        } catch (error) {
          // Summary doesn't exist yet, that's okay
          console.log('No summary found for document')
        }
      }
    } catch (error) {
      console.error('Failed to load document:', error)
      setError(error instanceof Error ? error.message : 'Failed to load document')
      toast.error('Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const generateSummary = async () => {
    if (!currentDocument) return

    setIsGeneratingSummary(true)
    try {
      const summary = await summaryApi.generateSummary(currentDocument.id)
      setCurrentSummary(summary)
      toast.success('Summary generated successfully!')
    } catch (error) {
      console.error('Failed to generate summary:', error)
      toast.error('Failed to generate summary')
    } finally {
      setIsGeneratingSummary(false)
    }
  }

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  const changePage = (offset: number) => {
    setPageNumber(prevPageNumber => {
      const newPageNumber = prevPageNumber + offset
      return Math.max(1, Math.min(newPageNumber, numPages))
    })
  }

  const changeScale = (delta: number) => {
    setScale(prevScale => Math.max(0.5, Math.min(prevScale + delta, 3)))
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    )
  }

  if (error || !currentDocument) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Document not found</h3>
        <p className="text-gray-500 mb-4">{error || 'The requested document could not be loaded.'}</p>
        <Link to="/" className="btn-primary">
          Back to Documents
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/"
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Documents</span>
          </Link>
          <div className="h-6 w-px bg-gray-300" />
          <h1 className="text-2xl font-bold text-gray-900 truncate">
            {currentDocument.originalName}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          {!currentSummary && (
            <button
              onClick={generateSummary}
              disabled={isGeneratingSummary}
              className="flex items-center space-x-2 btn-primary disabled:opacity-50"
            >
              {isGeneratingSummary ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              <span>{isGeneratingSummary ? 'Generating...' : 'Generate Summary'}</span>
            </button>
          )}
          
          {currentSummary && (
            <Link
              to={`/summary/${currentDocument.id}`}
              className="flex items-center space-x-2 bg-gold-500 hover:bg-gold-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              <Sparkles className="h-4 w-4" />
              <span>View Summary</span>
            </Link>
          )}

          <button className="btn-secondary">
            <Download className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* PDF Viewer */}
        <div className="lg:col-span-3">
          <div className="card p-4">
            {/* PDF Controls */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => changePage(-1)}
                    disabled={pageNumber <= 1}
                    className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {pageNumber} of {numPages}
                  </span>
                  <button
                    onClick={() => changePage(1)}
                    disabled={pageNumber >= numPages}
                    className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => changeScale(-0.2)}
                  className="p-2 text-gray-600 hover:text-gray-900"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-600 min-w-16 text-center">
                  {Math.round(scale * 100)}%
                </span>
                <button
                  onClick={() => changeScale(0.2)}
                  className="p-2 text-gray-600 hover:text-gray-900"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* PDF Document */}
            <div className="flex justify-center">
              <Document
                file={`/api/documents/${currentDocument.id}/file`}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                  </div>
                }
                error={
                  <div className="text-center py-12">
                    <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                    <p className="text-red-600">Failed to load PDF</p>
                  </div>
                }
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  loading={
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
                    </div>
                  }
                />
              </Document>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Document Info */}
          <div className="card p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Document Info</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Pages:</span>
                <span className="text-gray-900">{numPages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Size:</span>
                <span className="text-gray-900">{(currentDocument.fileSize / 1024 / 1024).toFixed(1)} MB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Uploaded:</span>
                <span className="text-gray-900">
                  {new Date(currentDocument.uploadedAt).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Summary Preview */}
          {currentSummary && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-4"
            >
              <div className="flex items-center space-x-2 mb-3">
                <Sparkles className="h-4 w-4 text-gold-500" />
                <h3 className="font-semibold text-gray-900">AI Summary</h3>
              </div>
              <p className="text-sm text-gray-600 line-clamp-6 mb-3">
                {currentSummary.content}
              </p>
              <Link
                to={`/summary/${currentDocument.id}`}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                View Full Summary →
              </Link>
            </motion.div>
          )}

          {/* Highlights */}
          {currentDocument.highlights && currentDocument.highlights.length > 0 && (
            <div className="card p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Key Highlights</h3>
              <div className="space-y-2">
                {currentDocument.highlights.slice(0, 3).map((highlight) => (
                  <div
                    key={highlight.id}
                    className="p-2 bg-gold-50 border border-gold-200 rounded text-xs cursor-pointer hover:bg-gold-100 transition-colors"
                    onClick={() => setPageNumber(highlight.pageNumber)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-gold-600 font-medium">Page {highlight.pageNumber}</span>
                      <span className="text-gold-500 capitalize">{highlight.type}</span>
                    </div>
                    <p className="text-gray-700 line-clamp-2">{highlight.text}</p>
                  </div>
                ))}
                {currentDocument.highlights.length > 3 && (
                  <p className="text-xs text-gray-500 text-center">
                    +{currentDocument.highlights.length - 3} more highlights
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
