from pydantic import BaseModel, Field
from typing import List, Optional, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

# Base schemas
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# Document schemas
class DocumentBase(BaseModel):
    filename: str
    original_name: str = Field(alias="originalName")
    file_size: int = Field(alias="fileSize")
    
    class Config:
        populate_by_name = True

class DocumentCreate(DocumentBase):
    file_path: str

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    processing_stage: Optional[str] = None
    processing_progress: Optional[int] = None
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    text_content: Optional[str] = None

class HighlightResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    x: float
    y: float
    width: float
    height: float
    text: str
    highlight_type: str = Field(alias="type")
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class SummaryResponse(BaseModel):
    id: str
    document_id: str
    content: str
    key_points: List[str] = []
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: str
    status: str
    processing_stage: Optional[str] = None
    processing_progress: Optional[int] = None
    page_count: Optional[int] = Field(default=None, alias="pageCount")
    uploaded_at: datetime = Field(alias="uploadedAt")
    processed_at: Optional[datetime] = Field(default=None, alias="processedAt")
    summary: Optional[SummaryResponse] = None
    highlights: List[HighlightResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Summary schemas
class SummaryCreate(BaseModel):
    document_id: str
    content: str
    key_points: List[str] = []
    processing_time: Optional[float] = None
    model_used: Optional[str] = None

# Highlight schemas
class HighlightCreate(BaseModel):
    document_id: str
    page_number: int
    x: float
    y: float
    width: float
    height: float
    text: str
    highlight_type: str
    confidence: Optional[float] = None

# Processing schemas
class ProcessingStatusResponse(BaseModel):
    document_id: str
    status: str
    stage: str
    progress: int
    message: str

class UploadProgressResponse(BaseModel):
    document_id: str
    progress: int
    status: str

# Search schemas
class SearchResult(BaseModel):
    document_id: str
    document_name: str
    relevance_score: float
    matched_text: str
    page_number: Optional[int] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float

# Vector embedding schemas
class EmbeddingCreate(BaseModel):
    document_id: str
    chunk_text: str
    chunk_index: int
    page_number: Optional[int] = None
    embedding: List[float]
    token_count: Optional[int] = None

# Job schemas
class ProcessingJobCreate(BaseModel):
    document_id: str
    job_type: str
    celery_task_id: Optional[str] = None

class ProcessingJobResponse(BaseModel):
    id: str
    document_id: str
    job_type: str
    status: str
    progress: int
    stage: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
