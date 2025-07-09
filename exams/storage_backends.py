import os
import json
import logging
from django.core.files.storage import Storage
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError
from google.api_core.exceptions import NotFound, ServiceUnavailable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        self._client = None
        self._bucket = None
        self._initialized = False

    def deconstruct(self):
        """
        Required for Django migrations to serialize the storage class
        """
        return (
            'exams.storage_backends.GoogleCloudMediaStorage',
            [],
            {}
        )

    def _initialize(self):
        """Lazy initialization of GCS client and bucket"""
        if not self._initialized:
            try:
                # Get credentials from environment variable
                credentials_json = os.environ.get('GCS_CREDENTIALS_JSON')
                if not credentials_json:
                    raise ValueError("GCS_CREDENTIALS_JSON environment variable not set")
                
                credentials_info = json.loads(credentials_json)
                bucket_name = os.environ.get('GS_BUCKET_NAME')
                if not bucket_name:
                    raise ValueError("GS_BUCKET_NAME environment variable not set")

                # Create credentials
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=["https://www.googleapis.com/auth/devstorage.full_control"]
                )

                # Initialize client and bucket
                self._client = storage.Client(
                    credentials=credentials,
                    project=credentials_info.get('project_id')
                )
                self._bucket = self._client.bucket(bucket_name)

                # Verify bucket exists
                if not self._bucket.exists():
                    raise ServiceUnavailable(f"Bucket {bucket_name} does not exist or is inaccessible")

                logger.info(f"Successfully connected to GCS bucket: {bucket_name}")
                self._initialized = True

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in credentials: {str(e)}")
                raise ValueError("Invalid GCS credentials configuration") from e
            except Exception as e:
                logger.error(f"Storage initialization error: {str(e)}")
                raise ServiceUnavailable(f"Storage service unavailable: {str(e)}") from e

    def _save(self, name, content):
        """Save file to GCS"""
        try:
            self._initialize()
            blob = self._bucket.blob(name)
            
            # Get content type if available
            content_type = getattr(content, 'content_type', None)
            
            blob.upload_from_file(
                content,
                content_type=content_type,
                timeout=300  # 5 minute timeout
            )
            return name
        except RefreshError as e:
            logger.error(f"Authentication token expired: {str(e)}")
            raise PermissionError("Google Cloud authentication token expired") from e
        except ServiceUnavailable as e:
            logger.error(f"GCS service unavailable: {str(e)}")
            raise ServiceUnavailable("Google Cloud Storage service is currently unavailable") from e
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise RuntimeError(f"File upload failed: {str(e)}") from e

    def exists(self, name):
        """Check if file exists in GCS"""
        try:
            self._initialize()
            return self._bucket.blob(name).exists()
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"Existence check failed: {str(e)}")
            raise ServiceUnavailable("Storage service unavailable") from e

    def url(self, name):
        """Get public URL for the file"""
        self._initialize()
        return f"https://storage.googleapis.com/{self._bucket.name}/{name}"

    def delete(self, name):
        """Delete file from GCS"""
        try:
            self._initialize()
            self._bucket.blob(name).delete()
        except Exception as e:
            logger.error(f"File deletion failed: {str(e)}")
            raise

    def size(self, name):
        """Get file size in bytes"""
        try:
            self._initialize()
            blob = self._bucket.blob(name)
            blob.reload()  # Refresh metadata
            return blob.size
        except Exception as e:
            logger.error(f"Size check failed: {str(e)}")
            raise

    def get_modified_time(self, name):
        """Get last modified time"""
        try:
            self._initialize()
            blob = self._bucket.blob(name)
            blob.reload()  # Refresh metadata
            return blob.updated
        except Exception as e:
            logger.error(f"Modified time check failed: {str(e)}")
            raise

    def path(self, name):
        """Not implemented for cloud storage"""
        raise NotImplementedError("Cloud storage doesn't support local paths")

    def open(self, name, mode='rb'):
        """Open file from GCS"""
        try:
            self._initialize()
            blob = self._bucket.blob(name)
            return blob.open(mode)
        except Exception as e:
            logger.error(f"File open failed: {str(e)}")
            raise

    def get_created_time(self, name):
        """Get creation time"""
        try:
            self._initialize()
            blob = self._bucket.blob(name)
            blob.reload()  # Refresh metadata
            return blob.time_created
        except Exception as e:
            logger.error(f"Created time check failed: {str(e)}")
            raise
