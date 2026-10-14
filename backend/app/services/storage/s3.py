"""Object storage client for MinIO / AWS S3 document ingestion."""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.storage")


class StorageService:
    """Service for uploading, downloading, and generating presigned URLs for documents."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region = region or settings.S3_REGION

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def generate_presigned_upload_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned PUT URL allowing clients to securely upload files directly."""
        try:
            return self.s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error("Failed to generate presigned upload URL for %s: %s", object_key, e)
            raise

    def generate_presigned_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL allowing clients to download or view a document."""
        try:
            return self.s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error("Failed to generate presigned download URL for %s: %s", object_key, e)
            raise

    def upload_bytes(self, data: bytes, object_key: str, content_type: str = "application/pdf") -> str:
        """Upload raw bytes to S3 and return the object key."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
            return object_key
        except ClientError as e:
            logger.error("Failed to upload bytes to %s: %s", object_key, e)
            raise

    def download_bytes(self, object_key: str) -> bytes:
        """Download raw object bytes from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Failed to download bytes from %s: %s", object_key, e)
            raise

    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in the bucket."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def delete_object(self, object_key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            logger.error("Failed to delete object %s: %s", object_key, e)
            return False


# Singleton instance
storage_service = StorageService()
