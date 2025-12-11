from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from typing import List, Optional
import uuid
import aiofiles
import logging
from pathlib import Path

from app.database import get_db, engine
from app.models import Base
from app.schemas import (
    DocumentResponse, 
    DocumentCreate, 
    SummaryResponse,
    PaginatedResponse,
    ProcessingStatusResponse
)
from app.services.document_service import DocumentService
from app.services.summary_service import SummaryService
from app.services.storage_service import StorageService
from app.config import settings
from app.celery_app import celery_app

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Summarizer AI",
    description="AI-powered document analysis and summarization platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://doc-summarizer-ai.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize services
document_service = DocumentService()
summary_service = SummaryService()
storage_service = StorageService()

@app.get("/")
async def root():
    return {
        "message": "Document Summarizer AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Document endpoints
@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF document for processing"""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size (50MB limit)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create document record
        document_data = DocumentCreate(
            filename=filename,
            original_name=file.filename,
            file_size=len(content),
            file_path=str(file_path)
        )
        
        document = await document_service.create_document(db, document_data)
        
        # Start background processing
        background_tasks.add_task(process_document_background, document.id, str(file_path))
        
        return DocumentResponse.from_orm(document)
        
    except Exception as e:
        # Clean up file if document creation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/documents", response_model=PaginatedResponse[DocumentResponse])
async def get_documents(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get paginated list of documents"""
    documents, total = await document_service.get_documents(db, page, page_size)
    
    return PaginatedResponse(
        items=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document by ID"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(document)

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete document and associated files"""
    success = await document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"success": True, "message": "Document deleted successfully"}

@app.get("/api/documents/{document_id}/file")
async def get_document_file(document_id: str, db: Session = Depends(get_db)):
    """Serve document file"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.original_name
    )

@app.get("/api/documents/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(document_id: str, db: Session = Depends(get_db)):
    """Get document processing status"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return ProcessingStatusResponse(
        document_id=document_id,
        status=document.status,
        stage=document.processing_stage or "pending",
        progress=document.processing_progress or 0,
        message=f"Document is {document.status}"
    )

# Summary endpoints
@app.post("/api/documents/{document_id}/summarize", response_model=SummaryResponse)
async def generate_summary(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Generate AI summary for document"""
    # Import services at the beginning
    from app.services.ai_service import AIService
    from app.services.summary_service import SummaryService
    from app.schemas import SummaryCreate
    import time
    
    ai_service = AIService()
    summary_service = SummaryService()
    
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != "completed":
        raise HTTPException(status_code=400, detail="Document is not ready for summarization")
    
    # Check if summary already exists
    existing_summary = await summary_service.get_summary_by_document_id(db, document_id)
    if existing_summary:
        return SummaryResponse.from_orm(existing_summary)
    
    # Generate summary directly (synchronously)
    try:
        
        logger.info(f"Generating summary for document: {document.original_name}")
        start_time = time.time()
        
        # Generate AI summary using Groq
        summary_result = await ai_service.generate_summary(
            document.text_content, 
            document.original_name,
            max_summary_length=500
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Summary generated in {processing_time:.2f} seconds")
        
        # Save summary to database
        summary_data = SummaryCreate(
            document_id=document_id,
            content=summary_result["summary"],
            key_points=summary_result.get("key_points", []),
            processing_time=processing_time,
            model_used=summary_result.get("model", "llama-3.3-70b-versatile")
        )
        
        new_summary = await summary_service.create_summary(db, summary_data)
        logger.info(f"Summary saved for document {document_id}")
        
        return SummaryResponse.from_orm(new_summary)
        
    except Exception as e:
        logger.error(f"Summary generation failed for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@app.get("/api/documents/{document_id}/summary", response_model=SummaryResponse)
async def get_summary(document_id: str, db: Session = Depends(get_db)):
    """Get summary for document"""
    summary = await summary_service.get_summary_by_document_id(db, document_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return SummaryResponse.from_orm(summary)

# Search endpoints
@app.get("/api/search")
async def search_documents(
    q: str,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Search documents by content"""
    # For now, implement basic text search
    # In production, this would use vector search with Pinecone
    documents, total = await document_service.search_documents(db, q, page, page_size)
    
    return PaginatedResponse(
        items=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )

@app.get("/api/documents/{document_id}/search")
async def search_in_document(
    document_id: str,
    q: str,
    db: Session = Depends(get_db)
):
    """Search within a specific document"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Implement semantic search within document
    results = await document_service.search_in_document(db, document_id, q)
    
    return {"results": results}

@app.post("/api/documents/{document_id}/process")
async def manually_process_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger processing for a document"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Start background processing
    background_tasks.add_task(process_document_background, document.id, document.file_path)
    
    return {"message": "Processing started", "document_id": document_id}

def generate_summary_background(document_id: str):
    """Background task to generate summary for document"""
    logger.info(f"Starting summary generation for document {document_id}")
    try:
        from app.services.ai_service import AIService
        from app.services.summary_service import SummaryService
        from app.database import SessionLocal
        from app.schemas import SummaryCreate
        import time
        
        ai_service = AIService()
        summary_service = SummaryService()
        
        # Create new database session for background task
        db = SessionLocal()
        
        try:
            import asyncio
            
            async def async_generate_summary():
                # Get document
                document = await document_service.get_document(db, document_id)
                if not document or not document.text_content:
                    raise Exception("Document not found or has no text content")
                
                logger.info(f"Generating summary for document: {document.original_name}")
                start_time = time.time()
                
                # Generate AI summary using Groq
                summary_result = await ai_service.generate_summary(
                    document.text_content, 
                    document.original_name,
                    max_summary_length=500
                )
                
                processing_time = time.time() - start_time
                logger.info(f"Summary generated in {processing_time:.2f} seconds")
                
                # Save summary to database
                summary_data = SummaryCreate(
                    document_id=document_id,
                    content=summary_result["summary"],
                    key_points=summary_result.get("key_points", []),
                    processing_time=processing_time,
                    model_used=summary_result.get("model", "llama-3.3-70b-versatile")
                )
                
                await summary_service.create_summary(db, summary_data)
                logger.info(f"Summary saved for document {document_id}")
            
            # Run the async function
            asyncio.run(async_generate_summary())
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Summary generation failed for {document_id}: {str(e)}")

async def process_document_background(document_id: str, file_path: str):
    """Background task to process uploaded document"""
    logger.info(f"Starting background processing for document {document_id}")
    try:
        # Simple processing without Celery for development
        from app.services.pdf_service import PDFService
        from app.services.ai_service import AIService
        from app.database import SessionLocal
        
        pdf_service = PDFService()
        ai_service = AIService()
        
        # Create new database session for background task
        db = SessionLocal()
        
        try:
            # Update status to processing
            await document_service.update_processing_status(
                db, document_id, "processing", "text-extraction", 25
            )
            
            # Extract text from PDF
            pdf_result = await pdf_service.extract_text_from_pdf(file_path)
            if not pdf_result.get('success'):
                raise Exception(f"PDF extraction failed: {pdf_result.get('error', 'Unknown error')}")
            
            text_content = pdf_result.get('text', '')
            page_count = pdf_result.get('page_count', 0)
            
            # Update document with extracted content
            await document_service.set_text_content(
                db, document_id, text_content, page_count
            )
            
            # Update status to completed
            await document_service.update_processing_status(
                db, document_id, "completed", "completed", 100
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {str(e)}")
        # Update status to error
        db = SessionLocal()
        try:
            await document_service.update_processing_status(
                db, document_id, "error", "failed", 0, str(e)
            )
        finally:
            db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
