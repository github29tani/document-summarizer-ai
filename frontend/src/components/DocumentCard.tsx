import { useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  FileText, 
  Calendar, 
  Download, 
  Trash2, 
  Eye, 
  Sparkles,
  Clock,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { motion } from 'framer-motion'
import { Document } from '@/types'
import { formatFileSize, formatDate } from '@/lib/utils'
import { documentApi } from '@/lib/api'
import { useDocumentStore } from '@/store/documentStore'
import toast from 'react-hot-toast'

interface DocumentCardProps {
  document: Document
  index: number
}

export function DocumentCard({ document, index }: DocumentCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const { removeDocument } = useDocumentStore()

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this document?')) return

    setIsDeleting(true)
    try {
      await documentApi.deleteDocument(document.id)
      removeDocument(document.id)
      toast.success('Document deleted successfully')
    } catch (error) {
      console.error('Delete error:', error)
      toast.error('Failed to delete document')
    } finally {
      setIsDeleting(false)
    }
  }

  const getStatusIcon = () => {
    switch (document.status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-gold-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusText = () => {
    switch (document.status) {
      case 'uploading':
        return 'Uploading...'
      case 'processing':
        return 'Processing...'
      case 'completed':
        return 'Ready'
      case 'error':
        return 'Error'
    }
  }

  const getStatusColor = () => {
    switch (document.status) {
      case 'uploading':
        return 'text-primary-600 bg-primary-50'
      case 'processing':
        return 'text-gold-600 bg-gold-50'
      case 'completed':
        return 'text-green-600 bg-green-50'
      case 'error':
        return 'text-red-600 bg-red-50'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="group"
    >
      <Link
        to={document.status === 'completed' ? `/document/${document.id}` : '#'}
        className={`block card p-6 transition-all duration-300 hover:shadow-lg ${
          document.status !== 'completed' ? 'cursor-default' : 'hover:shadow-xl'
        }`}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <FileText className="h-6 w-6 text-primary-600" />
              </div>
              {document.status === 'completed' && document.summary && (
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-gold-500 rounded-full flex items-center justify-center">
                  <Sparkles className="h-2 w-2 text-white" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate group-hover:text-primary-600 transition-colors">
                {document.originalName}
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                {getStatusIcon()}
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColor()}`}>
                  {getStatusText()}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {document.status === 'completed' && (
              <>
                <Link
                  to={`/document/${document.id}`}
                  className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                  title="View Document"
                >
                  <Eye className="h-4 w-4" />
                </Link>
                <button
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                  title="Download"
                >
                  <Download className="h-4 w-4" />
                </button>
              </>
            )}
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
              title="Delete"
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Document Info */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1">
                <Calendar className="h-4 w-4" />
                <span>{formatDate(document.uploadedAt)}</span>
              </span>
              <span>{formatFileSize(document.fileSize)}</span>
              {document.pageCount && (
                <span>{document.pageCount} pages</span>
              )}
            </div>
          </div>

          {/* Summary Preview */}
          {document.summary && (
            <div className="bg-gold-50 border border-gold-200 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <Sparkles className="h-4 w-4 text-gold-600" />
                <span className="text-sm font-medium text-gold-800">AI Summary Available</span>
              </div>
              <p className="text-sm text-gold-700 line-clamp-2">
                {document.summary.content.substring(0, 120)}...
              </p>
            </div>
          )}

          {/* Processing Status */}
          {document.status === 'processing' && (
            <div className="bg-gold-50 border border-gold-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-gold-600" />
                <span className="text-sm font-medium text-gold-800">
                  AI is analyzing your document...
                </span>
              </div>
              <div className="mt-2 w-full bg-gold-200 rounded-full h-2">
                <motion.div
                  className="bg-gold-500 h-2 rounded-full"
                  initial={{ width: '0%' }}
                  animate={{ width: '70%' }}
                  transition={{ duration: 2, repeat: Infinity, repeatType: 'reverse' }}
                />
              </div>
            </div>
          )}

          {/* Error Status */}
          {document.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm font-medium text-red-800">
                  Processing failed. Please try uploading again.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {document.status === 'completed' && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                {document.summary && (
                  <span className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>Summarized in {document.summary.processingTime}s</span>
                  </span>
                )}
                {document.highlights && (
                  <span>{document.highlights.length} highlights</span>
                )}
              </div>
              <span className="text-xs text-primary-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                Click to view →
              </span>
            </div>
          </div>
        )}
      </Link>
    </motion.div>
  )
}
