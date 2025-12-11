import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { documentApi } from '@/lib/api'
import { useDocumentStore } from '@/store/documentStore'
import { isValidPDF, formatFileSize } from '@/lib/utils'
import toast from 'react-hot-toast'

interface UploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}

export function DocumentUpload() {
  const [uploads, setUploads] = useState<UploadProgress[]>([])
  const { addDocument, setError } = useDocumentStore()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const validFiles = acceptedFiles.filter(file => {
      if (!isValidPDF(file)) {
        toast.error(`${file.name} is not a valid PDF file`)
        return false
      }
      if (file.size > 50 * 1024 * 1024) { // 50MB limit
        toast.error(`${file.name} is too large (max 50MB)`)
        return false
      }
      return true
    })

    if (validFiles.length === 0) return

    // Initialize upload progress for each file
    const newUploads: UploadProgress[] = validFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading'
    }))

    setUploads(prev => [...prev, ...newUploads])

    // Upload files sequentially
    for (const upload of newUploads) {
      try {
        const document = await documentApi.uploadDocument(
          upload.file,
          (progress) => {
            setUploads(prev => prev.map(u => 
              u.file === upload.file 
                ? { ...u, progress }
                : u
            ))
          }
        )

        // Update upload status to processing
        setUploads(prev => prev.map(u => 
          u.file === upload.file 
            ? { ...u, status: 'processing', progress: 100 }
            : u
        ))

        // Add document to store
        addDocument(document)

        // Mark as completed after a short delay
        setTimeout(() => {
          setUploads(prev => prev.map(u => 
            u.file === upload.file 
              ? { ...u, status: 'completed' }
              : u
          ))

          // Remove from uploads after 3 seconds
          setTimeout(() => {
            setUploads(prev => prev.filter(u => u.file !== upload.file))
          }, 3000)
        }, 1000)

        toast.success(`${upload.file.name} uploaded successfully`)

      } catch (error) {
        console.error('Upload error:', error)
        setUploads(prev => prev.map(u => 
          u.file === upload.file 
            ? { 
                ...u, 
                status: 'error', 
                error: error instanceof Error ? error.message : 'Upload failed'
              }
            : u
        ))
        
        setError(error instanceof Error ? error.message : 'Upload failed')
        toast.error(`Failed to upload ${upload.file.name}`)
      }
    }
  }, [addDocument, setError])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    maxSize: 50 * 1024 * 1024 // 50MB
  })

  const getStatusIcon = (status: UploadProgress['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusText = (upload: UploadProgress) => {
    switch (upload.status) {
      case 'uploading':
        return `Uploading... ${upload.progress}%`
      case 'processing':
        return 'Processing document...'
      case 'completed':
        return 'Upload completed'
      case 'error':
        return upload.error || 'Upload failed'
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
          isDragActive
            ? 'border-primary-400 bg-primary-50 scale-105'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
      >
        <motion.div
          className="w-full h-full"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <motion.div
            className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center"
            animate={isDragActive ? { scale: [1, 1.1, 1] } : {}}
            transition={{ duration: 0.5, repeat: isDragActive ? Infinity : 0 }}
          >
            <Upload className={`h-8 w-8 ${isDragActive ? 'text-primary-600' : 'text-primary-500'}`} />
          </motion.div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {isDragActive ? 'Drop your PDFs here' : 'Upload PDF Documents'}
            </h3>
            <p className="text-gray-600 mb-4">
              Drag and drop your PDF files here, or click to browse
            </p>
            <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
              <span>📄 PDF files only</span>
              <span>•</span>
              <span>Max 50MB per file</span>
              <span>•</span>
              <span>Multiple files supported</span>
            </div>
          </div>
        </div>

        {/* Scanning Animation Overlay */}
        <AnimatePresence>
          {isDragActive && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-primary-50 bg-opacity-50 rounded-xl flex items-center justify-center"
            >
              <motion.div
                animate={{ y: [-20, 20, -20] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="text-primary-600"
              >
                <FileText className="h-12 w-12 document-scan" />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
        </motion.div>
      </div>

      {/* Upload Progress */}
      <AnimatePresence>
        {uploads.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-3"
          >
            <h4 className="text-sm font-medium text-gray-700">Upload Progress</h4>
            {uploads.map((upload, index) => (
              <motion.div
                key={`${upload.file.name}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="card p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(upload.status)}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {upload.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(upload.file.size)}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {getStatusText(upload)}
                  </span>
                </div>
                
                {/* Progress Bar */}
                {(upload.status === 'uploading' || upload.status === 'processing') && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div
                      className={`h-2 rounded-full ${
                        upload.status === 'processing' 
                          ? 'bg-gold-500' 
                          : 'bg-primary-500'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ 
                        width: upload.status === 'processing' 
                          ? '100%' 
                          : `${upload.progress}%` 
                      }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
