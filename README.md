# Document Summarizer AI

A comprehensive document analysis and summarization platform built with modern AI technologies, featuring fast inference with Groq API and local embeddings.

## 🚀 Features

- **PDF Upload & Processing**: Drag-and-drop PDF upload with real-time processing
- **AI-Powered Summarization**: Advanced text summarization using LangChain + Groq API (llama-3.3-70b-versatile)
- **Interactive Highlighting**: Visual overlay highlighting for key sections
- **Vector Search**: Semantic search through document content using local embeddings
- **Background Processing**: Async document processing with Celery + Redis
- **Professional UI**: Clean, modern interface with document scanning animations
- **Fast Inference**: Lightning-fast AI responses powered by Groq's optimized infrastructure

## 🛠 Tech Stack

### Frontend
- React + TypeScript
- React PDF for document viewing
- Lucide React Icons for UI elements
- TailwindCSS for styling
- Vite for build tooling
- Framer Motion for animations
- React Router for navigation
- Zustand for state management

### Backend
- Python FastAPI
- Celery + Redis for background tasks
- SQLite/PostgreSQL for metadata storage
- AWS S3 for file storage
- Pydantic for data validation

### AI/ML
- LangChain for document processing
- **Groq API** for fast text summarization (llama-3.3-70b-versatile model)
- **SentenceTransformers** for local embeddings (all-MiniLM-L6-v2)
- Pinecone Vector Database for semantic search
- PyPDF2 for text extraction
- Tiktoken for token counting

### Deployment
- Frontend: Vercel
- Backend: Railway
- Storage: AWS S3

## 🎨 Visual Theme

- **Colors**: Professional gray (#374151) + Blue (#2563eb) + Gold accents (#f59e0b)
- **Style**: Clean document interface with highlighting
- **Icons**: 📄🔍💡 with scanning animations

## ⚙️ Environment Setup

1. **Copy environment variables**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your `.env` file** with the following required variables:
   ```env
   # Groq API (Required for AI summarization)
   GROQ_API_KEY=your_groq_api_key_here
   
   # Pinecone (Optional - for vector search)
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment
   
   # AWS S3 (Optional - for file storage)
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   S3_BUCKET_NAME=your_s3_bucket_name
   
   # Database (Optional - defaults to SQLite)
   DATABASE_URL=sqlite:///./document_summarizer.db
   
   # Redis (Required for background tasks)
   REDIS_URL=redis://localhost:6379
   ```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Redis server (for background tasks)
- Groq API key ([Get one here](https://console.groq.com/))

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Redis server (if not running)
redis-server

# Start Celery worker (in a separate terminal)
celery -A main.celery worker --loglevel=info

# Start the FastAPI server
uvicorn main:app --reload --port 8001
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

## 📁 Project Structure

```
document-summarizer-ai/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API service functions
│   │   ├── store/           # Zustand state management
│   │   └── types/           # TypeScript type definitions
│   ├── public/              # Static assets
│   └── package.json
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API route handlers
│   │   ├── core/            # Core functionality
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic services
│   │   └── utils/           # Utility functions
│   ├── uploads/             # File upload directory
│   ├── main.py              # FastAPI application entry point
│   └── requirements.txt     # Python dependencies
├── .env.example             # Environment variables template
└── README.md
```

## 🔧 Key Features Explained

### AI-Powered Summarization
- Uses Groq's **llama-3.3-70b-versatile** model for fast, high-quality text summarization
- Processes documents in chunks for optimal performance
- Maintains context across document sections

### Local Embeddings
- **SentenceTransformers** (all-MiniLM-L6-v2) for generating document embeddings
- No external API calls for embedding generation
- Privacy-focused approach with local processing

### Background Processing
- **Celery** workers handle document processing asynchronously
- **Redis** as message broker for task queuing
- Real-time progress updates via WebSocket connections

### Vector Search
- **Pinecone** integration for semantic document search
- Find relevant sections based on meaning, not just keywords
- Supports similarity search across document collections
