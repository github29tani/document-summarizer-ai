from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Tuple, Optional
from pathlib import Path
import os

from app.models import Document, Summary, Highlight
from app.schemas import DocumentCreate, DocumentUpdate
from app.services.storage_service import StorageService

class DocumentService:
    def __init__(self):
        self.storage_service = StorageService()

    async def create_document(self, db: Session, document_data: DocumentCreate) -> Document:
        """Create a new document record"""
        document = Document(
            filename=document_data.filename,
            original_name=document_data.original_name,
            file_size=document_data.file_size,
            file_path=document_data.file_path,
            status="uploading"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document

    async def get_document(self, db: Session, document_id: str) -> Optional[Document]:
        """Get document by ID with related data"""
        return db.query(Document).filter(Document.id == document_id).first()

    async def get_documents(
        self, 
        db: Session, 
        page: int = 1, 
        page_size: int = 10
    ) -> Tuple[List[Document], int]:
        """Get paginated list of documents"""
        offset = (page - 1) * page_size
        
        query = db.query(Document).order_by(desc(Document.uploaded_at))
        total = query.count()
        documents = query.offset(offset).limit(page_size).all()
        
        return documents, total

    async def update_document(
        self, 
        db: Session, 
        document_id: str, 
        updates: DocumentUpdate
    ) -> Optional[Document]:
        """Update document with new data"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        
        db.commit()
        db.refresh(document)
        
        return document

    async def delete_document(self, db: Session, document_id: str) -> bool:
        """Delete document and associated files"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return False
        
        # Delete physical file
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        # Delete from S3 if exists
        if document.s3_key:
            try:
                await self.storage_service.delete_file(document.s3_key)
            except Exception as e:
                print(f"Error deleting from S3: {e}")
        
        # Delete database record (cascades to summaries and highlights)
        db.delete(document)
        db.commit()
        
        return True

    async def search_documents(
        self, 
        db: Session, 
        query: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> Tuple[List[Document], int]:
        """Search documents by name or content"""
        offset = (page - 1) * page_size
        
        # Basic text search - in production, use full-text search or vector search
        search_filter = or_(
            Document.original_name.ilike(f"%{query}%"),
            Document.text_content.ilike(f"%{query}%")
        )
        
        db_query = db.query(Document).filter(search_filter).order_by(desc(Document.uploaded_at))
        total = db_query.count()
        documents = db_query.offset(offset).limit(page_size).all()
        
        return documents, total

    async def search_in_document(
        self, 
        db: Session, 
        document_id: str, 
        query: str
    ) -> List[dict]:
        """Search within a specific document"""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document or not document.text_content:
            return []
        
        # Simple text search within document
        # In production, this would use vector embeddings for semantic search
        results = []
        text = document.text_content.lower()
        query_lower = query.lower()
        
        # Find all occurrences
        start = 0
        while True:
            pos = text.find(query_lower, start)
            if pos == -1:
                break
            
            # Extract context around the match
            context_start = max(0, pos - 100)
            context_end = min(len(text), pos + len(query) + 100)
            context = document.text_content[context_start:context_end]
            
            results.append({
                "position": pos,
                "context": context,
                "relevance_score": 1.0  # Simple scoring
            })
            
            start = pos + 1
            
            # Limit results
            if len(results) >= 10:
                break
        
        return results

    async def update_processing_status(
        self, 
        db: Session, 
        document_id: str, 
        status: str, 
        stage: Optional[str] = None, 
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """Update document processing status"""
        updates = DocumentUpdate(
            status=status,
            processing_stage=stage,
            processing_progress=progress,
            error_message=error_message
        )
        
        return await self.update_document(db, document_id, updates)

    async def set_text_content(
        self, 
        db: Session, 
        document_id: str, 
        text_content: str, 
        page_count: int
    ) -> Optional[Document]:
        """Set extracted text content for document"""
        updates = DocumentUpdate(
            text_content=text_content,
            page_count=page_count
        )
        
        return await self.update_document(db, document_id, updates)

    async def get_documents_by_status(
        self, 
        db: Session, 
        status: str
    ) -> List[Document]:
        """Get documents by status"""
        return db.query(Document).filter(Document.status == status).all()

    async def get_processing_stats(self, db: Session) -> dict:
        """Get processing statistics"""
        total = db.query(Document).count()
        completed = db.query(Document).filter(Document.status == "completed").count()
        processing = db.query(Document).filter(Document.status == "processing").count()
        error = db.query(Document).filter(Document.status == "error").count()
        
        return {
            "total": total,
            "completed": completed,
            "processing": processing,
            "error": error,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
