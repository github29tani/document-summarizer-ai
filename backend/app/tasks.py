from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, List
import traceback
import logging
import asyncio

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Document
from app.services.document_service import DocumentService
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.summary_service import SummaryService
from app.services.storage_service import StorageService
from app.schemas import SummaryCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
document_service = DocumentService()
pdf_service = PDFService()
ai_service = AIService()
summary_service = SummaryService()
storage_service = StorageService()

@celery_app.task(bind=True, name='app.tasks.process_document_task')
def process_document_task(self, document_id: str, file_path: str):
    """
    Background task to process uploaded PDF document
    - Extract text content
    - Generate embeddings
    - Update document status
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting document processing for document {document_id}")
        
        # Update status to processing
        asyncio.run(document_service.update_processing_status(
            db, document_id, "processing", "text_extraction", 10
        ))
        
        # Step 1: Extract text from PDF
        logger.info(f"Extracting text from PDF: {file_path}")
        extraction_result = asyncio.run(pdf_service.extract_text_from_pdf(file_path))
        
        if not extraction_result["success"]:
            raise Exception(f"PDF text extraction failed: {extraction_result['error']}")
        
        # Update document with extracted text
        asyncio.run(document_service.set_text_content(
            db, 
            document_id, 
            extraction_result["text"], 
            extraction_result["page_count"]
        ))
        
        # Update progress
        asyncio.run(document_service.update_processing_status(
            db, document_id, "processing", "text_processing", 40
        ))
        
        # Step 2: Upload to S3 (if configured)
        try:
            logger.info(f"Uploading document to S3")
            s3_key = f"documents/{document_id}.pdf"
            s3_url = storage_service.upload_file(file_path, s3_key)
            
            # Update document with S3 info
            from app.schemas import DocumentUpdate
            updates = DocumentUpdate(s3_key=s3_key, s3_url=s3_url)
            asyncio.run(document_service.update_document(db, document_id, updates))
            
        except Exception as e:
            logger.warning(f"S3 upload failed (continuing without S3): {e}")
        
        # Update progress
        asyncio.run(document_service.update_processing_status(
            db, document_id, "processing", "generating_embeddings", 70
        ))
        
        # Step 3: Generate embeddings for semantic search
        if extraction_result["text"]:
            try:
                # Split text into chunks for embedding
                chunks = pdf_service.get_text_chunks(
                    extraction_result["text"], 
                    chunk_size=1000, 
                    overlap=100
                )
                
                # Generate embeddings for chunks
                chunk_texts = [chunk["text"] for chunk in chunks]
                embeddings = asyncio.run(ai_service.generate_embeddings(chunk_texts))
                
                # Store embeddings (in production, this would go to Pinecone)
                # For now, we'll store them in the document metadata
                embedding_data = [
                    {
                        "chunk_index": i,
                        "text": chunk["text"],
                        "embedding": embedding,
                        "word_count": chunk["word_count"]
                    }
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                
                # Update document with embedding metadata
                from app.schemas import DocumentUpdate
                updates = DocumentUpdate(
                    embedding_metadata={
                        "chunks": len(chunks),
                        "embeddings_generated": True,
                        "model": "text-embedding-ada-002"
                    }
                )
                asyncio.run(document_service.update_document(db, document_id, updates))
                
                logger.info(f"Generated embeddings for {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                # Continue without embeddings
        
        # Step 4: Final status update
        asyncio.run(document_service.update_processing_status(
            db, document_id, "completed", "completed", 100
        ))
        
        logger.info(f"Document processing completed for document {document_id}")
        
        return {
            "status": "success",
            "document_id": document_id,
            "text_length": len(extraction_result["text"]),
            "page_count": extraction_result["page_count"],
            "word_count": extraction_result["word_count"]
        }
        
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update status to error
        asyncio.run(document_service.update_processing_status(
            db, 
            document_id, 
            "error", 
            "error", 
            0, 
            error_message=str(e)
        ))
        
        # Re-raise the exception to mark task as failed
        raise e
        
    finally:
        db.close()

@celery_app.task(bind=True, name='app.tasks.generate_summary_task')
def generate_summary_task(self, document_id: str):
    """
    Background task to generate AI summary for a document
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting summary generation for document {document_id}")
        
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        if not document.text_content:
            raise Exception(f"Document {document_id} has no text content")
        
        # Check if summary already exists
        existing_summary = summary_service.get_summary_by_document_id(db, document_id)
        if existing_summary:
            logger.info(f"Summary already exists for document {document_id}")
            return {
                "status": "exists",
                "summary_id": existing_summary.id
            }
        
        # Generate AI summary
        logger.info(f"Generating AI summary for document: {document.original_name}")
        
        summary_result = ai_service.generate_summary(
            text=document.text_content,
            document_name=document.original_name,
            max_summary_length=500
        )
        
        # Extract highlights
        highlights = ai_service.extract_highlights(
            text=document.text_content,
            summary=summary_result["summary"]
        )
        
        # Create summary record
        summary_data = SummaryCreate(
            document_id=document_id,
            content=summary_result["summary"],
            key_points=summary_result.get("key_points", []),
            model_used=summary_result.get("model", "gpt-3.5-turbo"),
            processing_time=None  # Could be calculated if needed
        )
        
        summary = summary_service.create_summary(db, summary_data)
        
        logger.info(f"Summary generated successfully for document {document_id}")
        
        return {
            "status": "success",
            "summary_id": summary.id,
            "document_id": document_id,
            "summary_length": len(summary_result["summary"]),
            "key_points_count": len(summary_result.get("key_points", [])),
            "highlights_count": len(highlights)
        }
        
    except Exception as e:
        logger.error(f"Summary generation failed for {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Re-raise the exception to mark task as failed
        raise e
        
    finally:
        db.close()

@celery_app.task(bind=True, name='app.tasks.generate_embeddings_task')
def generate_embeddings_task(self, document_id: str, chunk_size: int = 1000):
    """
    Background task to generate embeddings for document chunks
    Used for semantic search capabilities
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting embedding generation for document {document_id}")
        
        # Get document
        document = document_service.get_document(db, document_id)
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        if not document.text_content:
            raise Exception(f"Document {document_id} has no text content")
        
        # Split text into chunks
        chunks = pdf_service.get_text_chunks(
            document.text_content, 
            chunk_size=chunk_size, 
            overlap=100
        )
        
        logger.info(f"Split document into {len(chunks)} chunks")
        
        # Generate embeddings
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = ai_service.generate_embeddings(chunk_texts)
        
        # Prepare embedding data
        embedding_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_data.append({
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk["text"],
                "embedding": embedding,
                "word_count": chunk["word_count"],
                "start_word": chunk["start_word"],
                "end_word": chunk["end_word"]
            })
        
        # In production, store embeddings in Pinecone or similar vector database
        # For now, we'll update the document with embedding metadata
        from app.schemas import DocumentUpdate
        updates = DocumentUpdate(
            embedding_metadata={
                "chunks": len(chunks),
                "embeddings_generated": True,
                "model": "text-embedding-ada-002",
                "chunk_size": chunk_size,
                "total_embeddings": len(embeddings)
            }
        )
        document_service.update_document(db, document_id, updates)
        
        logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_processed": len(chunks),
            "embeddings_generated": len(embeddings),
            "model": "text-embedding-ada-002"
        }
        
    except Exception as e:
        logger.error(f"Embedding generation failed for {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Re-raise the exception to mark task as failed
        raise e
        
    finally:
        db.close()

@celery_app.task(bind=True, name='app.tasks.cleanup_failed_documents')
def cleanup_failed_documents(self):
    """
    Periodic task to clean up documents that failed processing
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting cleanup of failed documents")
        
        # Get documents that have been in error state for more than 1 hour
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        failed_documents = db.query(Document).filter(
            and_(
                Document.status == "error",
                Document.updated_at < cutoff_time
            )
        ).all()
        
        cleaned_count = 0
        for document in failed_documents:
            try:
                # Delete the document (this will also clean up files)
                success = document_service.delete_document(db, document.id)
                if success:
                    cleaned_count += 1
                    logger.info(f"Cleaned up failed document: {document.id}")
            except Exception as e:
                logger.error(f"Failed to clean up document {document.id}: {e}")
        
        logger.info(f"Cleanup completed. Removed {cleaned_count} failed documents")
        
        return {
            "status": "success",
            "cleaned_documents": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise e
        
    finally:
        db.close()

@celery_app.task(bind=True, name='app.tasks.update_document_stats')
def update_document_stats(self):
    """
    Periodic task to update document processing statistics
    """
    db = SessionLocal()
    
    try:
        logger.info("Updating document processing statistics")
        
        stats = document_service.get_processing_stats(db)
        
        # In production, you might store these stats in Redis or a monitoring system
        logger.info(f"Document stats: {stats}")
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Stats update task failed: {str(e)}")
        raise e
        
    finally:
        db.close()
