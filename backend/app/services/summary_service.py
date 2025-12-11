from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import time

from app.models import Summary, Document
from app.schemas import SummaryCreate
from app.services.ai_service import AIService

class SummaryService:
    def __init__(self):
        self.ai_service = AIService()

    async def create_summary(self, db: Session, summary_data: SummaryCreate) -> Summary:
        """Create a new summary record"""
        summary = Summary(
            document_id=summary_data.document_id,
            content=summary_data.content,
            key_points=summary_data.key_points,
            processing_time=summary_data.processing_time,
            model_used=summary_data.model_used
        )
        
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        return summary

    async def get_summary_by_document_id(self, db: Session, document_id: str) -> Optional[Summary]:
        """Get summary by document ID"""
        return db.query(Summary).filter(Summary.document_id == document_id).first()

    async def get_summary(self, db: Session, summary_id: str) -> Optional[Summary]:
        """Get summary by ID"""
        return db.query(Summary).filter(Summary.id == summary_id).first()

    async def generate_summary(self, db: Session, document_id: str) -> Summary:
        """Generate AI summary for document"""
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")
        
        if not document.text_content:
            raise ValueError("Document has no text content")
        
        # Check if summary already exists
        existing_summary = await self.get_summary_by_document_id(db, document_id)
        if existing_summary:
            return existing_summary
        
        # Generate summary using AI service
        start_time = time.time()
        
        try:
            summary_result = await self.ai_service.generate_summary(
                text=document.text_content,
                document_name=document.original_name
            )
            
            processing_time = time.time() - start_time
            
            # Create summary record
            summary_data = SummaryCreate(
                document_id=document_id,
                content=summary_result["summary"],
                key_points=summary_result.get("key_points", []),
                processing_time=processing_time,
                model_used=summary_result.get("model", "gpt-3.5-turbo")
            )
            
            summary = await self.create_summary(db, summary_data)
            
            return summary
            
        except Exception as e:
            raise Exception(f"Failed to generate summary: {str(e)}")

    async def update_summary(
        self, 
        db: Session, 
        summary_id: str, 
        content: Optional[str] = None,
        key_points: Optional[List[str]] = None
    ) -> Optional[Summary]:
        """Update summary content"""
        summary = db.query(Summary).filter(Summary.id == summary_id).first()
        if not summary:
            return None
        
        if content is not None:
            summary.content = content
        if key_points is not None:
            summary.key_points = key_points
        
        db.commit()
        db.refresh(summary)
        
        return summary

    async def delete_summary(self, db: Session, summary_id: str) -> bool:
        """Delete summary"""
        summary = db.query(Summary).filter(Summary.id == summary_id).first()
        if not summary:
            return False
        
        db.delete(summary)
        db.commit()
        
        return True

    async def get_summaries_by_date_range(
        self, 
        db: Session, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Summary]:
        """Get summaries created within date range"""
        return db.query(Summary).filter(
            Summary.created_at >= start_date,
            Summary.created_at <= end_date
        ).all()

    async def get_summary_stats(self, db: Session) -> dict:
        """Get summary statistics"""
        total_summaries = db.query(Summary).count()
        
        if total_summaries == 0:
            return {
                "total_summaries": 0,
                "average_processing_time": 0,
                "total_processing_time": 0
            }
        
        # Calculate average processing time
        summaries = db.query(Summary).filter(Summary.processing_time.isnot(None)).all()
        processing_times = [s.processing_time for s in summaries if s.processing_time]
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        total_processing_time = sum(processing_times) if processing_times else 0
        
        return {
            "total_summaries": total_summaries,
            "average_processing_time": round(avg_processing_time, 2),
            "total_processing_time": round(total_processing_time, 2),
            "summaries_with_timing": len(processing_times)
        }
