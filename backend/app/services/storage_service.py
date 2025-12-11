import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from pathlib import Path
import aiofiles
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import settings

class StorageService:
    def __init__(self):
        self.s3_client = None
        self.bucket_name = settings.s3_bucket_name
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize S3 client if credentials are available
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )

    async def upload_file(self, file_path: str, s3_key: str) -> bool:
        """Upload file to S3 storage"""
        if not self.s3_client:
            return False
        
        try:
            # Run S3 upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._upload_file_sync,
                file_path,
                s3_key
            )
            return True
            
        except Exception as e:
            print(f"S3 upload error: {e}")
            return False

    def _upload_file_sync(self, file_path: str, s3_key: str):
        """Synchronous S3 upload"""
        self.s3_client.upload_file(
            file_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )

    async def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3 storage"""
        if not self.s3_client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._download_file_sync,
                s3_key,
                local_path
            )
            return True
            
        except Exception as e:
            print(f"S3 download error: {e}")
            return False

    def _download_file_sync(self, s3_key: str, local_path: str):
        """Synchronous S3 download"""
        self.s3_client.download_file(
            self.bucket_name,
            s3_key,
            local_path
        )

    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3 storage"""
        if not self.s3_client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._delete_file_sync,
                s3_key
            )
            return True
            
        except Exception as e:
            print(f"S3 delete error: {e}")
            return False

    def _delete_file_sync(self, s3_key: str):
        """Synchronous S3 delete"""
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )

    async def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        if not self.s3_client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._file_exists_sync,
                s3_key
            )
            return True
            
        except ClientError:
            return False

    def _file_exists_sync(self, s3_key: str):
        """Synchronous S3 file existence check"""
        self.s3_client.head_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )

    async def get_file_url(self, s3_key: str, expires_in: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        if not self.s3_client:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                self.executor,
                self._generate_presigned_url_sync,
                s3_key,
                expires_in
            )
            return url
            
        except Exception as e:
            print(f"Presigned URL error: {e}")
            return None

    def _generate_presigned_url_sync(self, s3_key: str, expires_in: int) -> str:
        """Synchronous presigned URL generation"""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': s3_key},
            ExpiresIn=expires_in
        )

    def get_s3_key(self, document_id: str, filename: str) -> str:
        """Generate S3 key for document"""
        return f"documents/{document_id}/{filename}"

    async def cleanup_local_file(self, file_path: str) -> bool:
        """Clean up local file after S3 upload"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            print(f"Local file cleanup error: {e}")
            return False
