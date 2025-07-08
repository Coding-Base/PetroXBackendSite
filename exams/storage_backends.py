import os
import json
import logging
from django.core.files.storage import Storage
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError, DefaultCredentialsError
from google.api_core.exceptions import NotFound, ServiceUnavailable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        try:
            # Validate environment variables
            if "GCS_CREDENTIALS_JSON" not in os.environ:
                raise ValueError("GCS_CREDENTIALS_JSON environment variable not set")
            if "GS_BUCKET_NAME" not in os.environ:
                raise ValueError("GS_BUCKET_NAME environment variable not set")
                
            credentials_info = json.loads(os.environ["GCS_CREDENTIALS_JSON"])
            bucket_name = os.environ["GS_BUCKET_NAME"]
            
            # Check system time synchronization
            current_time = datetime.now(timezone.utc)
            logger.info(f"Current system time: {current_time}")
            
            # Create credentials with explicit scopes
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/devstorage.full_control"]
            )
            
            self.client = storage.Client(
                credentials=credentials,
                project=credentials_info.get('project_id')
            )
            self.bucket = self.client.bucket(bucket_name)
            
            # Verify bucket accessibility
            if not self.bucket.exists():
                raise ServiceUnavailable(f"Bucket {bucket_name} does not exist or is inaccessible")
                
            logger.info(f"Successfully connected to GCS bucket: {bucket_name}")
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid credentials configuration: {str(e)}")
            raise ValueError("Invalid GCS credentials configuration") from e
        except DefaultCredentialsError as e:
            logger.error(f"Google authentication error: {str(e)}")
            raise PermissionError("Google Cloud authentication failed") from e
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            raise ServiceUnavailable(f"Storage service unavailable: {str(e)}") from e

    def _save(self, name, content):
        try:
            blob = self.bucket.blob(name)
            blob.upload_from_file(
                content,
                content_type=content.content_type,
                timeout=300  # Increase timeout for large files
            )
            return name
        except RefreshError as e:
            logger.error(f"JWT token refresh failed: {str(e)}")
            raise PermissionError("Google Cloud authentication token expired") from e
        except ServiceUnavailable as e:
            logger.error(f"GCS service unavailable: {str(e)}")
            raise ServiceUnavailable("Google Cloud Storage service is currently unavailable") from e
        except Exception as e:
            logger.error(f"GCS upload error: {str(e)}")
            raise RuntimeError(f"File upload failed: {str(e)}") from e

    def exists(self, name):
        try:
            return self.bucket.blob(name).exists()
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"GCS existence check error: {str(e)}")
            raise ServiceUnavailable("Storage service unavailable") from e

    def url(self, name):
        return f"https://storage.googleapis.com/{self.bucket.name}/{name}"

    def delete(self, name):
        try:
            self.bucket.blob(name).delete()
        except Exception as e:
            logger.error(f"GCS delete error: {str(e)}")
            raise e

    def size(self, name):
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.size
        except Exception as e:
            logger.error(f"GCS size check error: {str(e)}")
            raise e

    def get_modified_time(self, name):
        try:
            blob = self.bucket.blob(name)
            blob.reload()
            return blob.updated
        except Exception as e:
            logger.error(f"GCS modified time check error: {str(e)}")
            raise e

    def path(self, name):
        """
        This method is not implemented for cloud storage
        """
        raise NotImplementedError("Cloud storage doesn't support local paths")

    def open(self, name, mode='rb'):
        """
        This method is not implemented for cloud storage
        """
        raise NotImplementedError("Cloud storage doesn't support direct file opening")
