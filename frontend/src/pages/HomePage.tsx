import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  FileText, 
  Search, 
  Sparkles, 
  TrendingUp,
  Clock,
  Filter,
  Grid,
  List
} from 'lucide-react'
import { DocumentUpload } from '@/components/DocumentUpload'
import { DocumentCard } from '@/components/DocumentCard'
import { useDocumentStore } from '@/store/documentStore'
import { documentApi } from '@/lib/api'
import toast from 'react-hot-toast'

type ViewMode = 'grid' | 'list'
type SortBy = 'recent' | 'name' | 'size'
type FilterBy = 'all' | 'completed' | 'processing' | 'error'

export function HomePage() {
  const { 
    documents, 
    setDocuments, 
    isLoading, 
    setLoading, 
    error, 
    setError 
  } = useDocumentStore()
  
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filterBy, setFilterBy] = useState<FilterBy>('all')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await documentApi.getDocuments()
      setDocuments(response.items)
    } catch (error) {
      console.error('Failed to load documents:', error)
      setError(error instanceof Error ? error.message : 'Failed to load documents')
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort documents
  const filteredAndSortedDocuments = documents
    .filter(doc => {
      // Filter by status
      if (filterBy !== 'all' && doc.status !== filterBy) return false
      
      // Filter by search query
      if (searchQuery && !doc.originalName.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime()
        case 'name':
          return a.originalName.localeCompare(b.originalName)
        case 'size':
          return b.fileSize - a.fileSize
        default:
          return 0
      }
    })

  const stats = {
    total: documents.length,
    completed: documents.filter(d => d.status === 'completed').length,
    processing: documents.filter(d => d.status === 'processing').length,
    withSummary: documents.filter(d => d.summary).length,
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <div className="flex items-center justify-center space-x-3 mb-4">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="relative"
          >
            <Sparkles className="h-8 w-8 text-gold-500" />
          </motion.div>
          <h1 className="text-4xl font-bold text-gray-900">
            Document Summarizer AI
          </h1>
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="relative"
          >
            <FileText className="h-8 w-8 text-primary-500" />
          </motion.div>
        </div>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your PDF documents and get AI-powered summaries with intelligent highlighting
        </p>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-6"
      >
        <div className="card p-6 text-center">
          <FileText className="h-8 w-8 text-primary-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-sm text-gray-500">Total Documents</div>
        </div>
        <div className="card p-6 text-center">
          <TrendingUp className="h-8 w-8 text-green-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{stats.completed}</div>
          <div className="text-sm text-gray-500">Processed</div>
        </div>
        <div className="card p-6 text-center">
          <Clock className="h-8 w-8 text-gold-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{stats.processing}</div>
          <div className="text-sm text-gray-500">Processing</div>
        </div>
        <div className="card p-6 text-center">
          <Sparkles className="h-8 w-8 text-gold-500 mx-auto mb-2" />
          <div className="text-2xl font-bold text-gray-900">{stats.withSummary}</div>
          <div className="text-sm text-gray-500">With AI Summary</div>
        </div>
      </motion.div>

      {/* Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <DocumentUpload />
      </motion.div>

      {/* Documents Section */}
      {documents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          {/* Section Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <h2 className="text-2xl font-bold text-gray-900">Your Documents</h2>
            
            {/* Controls */}
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent w-64"
                />
              </div>

              {/* Filters */}
              <select
                value={filterBy}
                onChange={(e) => setFilterBy(e.target.value as FilterBy)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="error">Error</option>
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="recent">Most Recent</option>
                <option value="name">Name</option>
                <option value="size">File Size</option>
              </select>

              {/* View Mode Toggle */}
              <div className="flex items-center border border-gray-300 rounded-lg">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-primary-500 text-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <Grid className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-primary-500 text-white' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Documents Grid/List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              <span className="ml-3 text-gray-600">Loading documents...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-500 mb-2">Failed to load documents</div>
              <button
                onClick={loadDocuments}
                className="btn-primary"
              >
                Try Again
              </button>
            </div>
          ) : filteredAndSortedDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchQuery || filterBy !== 'all' ? 'No documents match your criteria' : 'No documents yet'}
              </h3>
              <p className="text-gray-500">
                {searchQuery || filterBy !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Upload your first PDF document to get started'
                }
              </p>
            </div>
          ) : (
            <div className={
              viewMode === 'grid' 
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                : 'space-y-4'
            }>
              {filteredAndSortedDocuments.map((document, index) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  index={index}
                />
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
