from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    s3_key = Column(String, nullable=True)  # For S3 storage
    
    # Processing status
    status = Column(String, default="uploading")  # uploading, processing, completed, error
    processing_stage = Column(String, nullable=True)  # text-extraction, summarization, highlighting
    processing_progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Document metadata
    page_count = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    summaries = relationship("Summary", back_populates="document", cascade="all, delete-orphan")
    highlights = relationship("Highlight", back_populates="document", cascade="all, delete-orphan")

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    
    # Summary content
    content = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)  # List of key points
    
    # Processing metadata
    processing_time = Column(Float, nullable=True)  # Time in seconds
    model_used = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="summaries")

class Highlight(Base):
    __tablename__ = "highlights"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    
    # Position information
    page_number = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    highlight_type = Column(String, nullable=False)  # key-point, important, definition
    confidence = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="highlights")

class VectorEmbedding(Base):
    __tablename__ = "vector_embeddings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    
    # Text chunk information
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    
    # Vector data (stored as JSON for PostgreSQL)
    embedding = Column(JSON, nullable=False)
    
    # Metadata
    token_count = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    
    # Job information
    job_type = Column(String, nullable=False)  # text_extraction, summarization, embedding
    status = Column(String, default="pending")  # pending, running, completed, failed
    
    # Progress tracking
    progress = Column(Integer, default=0)
    stage = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    
    # Celery task information
    celery_task_id = Column(String, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
