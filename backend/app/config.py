from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./document_summarizer.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Groq
    groq_api_key: str = ""
    
    # Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east1-gcp"
    pinecone_index_name: str = "document-summarizer"
    
    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket_name: str = ""
    aws_region: str = "us-east-1"
    
    # File upload settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: list = ["application/pdf"]
    upload_dir: str = "uploads"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379"
    celery_result_backend: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = "../.env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate that required settings are present"""
    required_for_ai = ["groq_api_key"]
    missing = [key for key in required_for_ai if not getattr(settings, key)]
    
    if missing and settings.environment == "production":
        raise ValueError(f"Missing required settings: {', '.join(missing)}")

# Call validation
validate_settings()
