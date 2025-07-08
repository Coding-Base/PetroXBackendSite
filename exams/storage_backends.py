import os
import json
import logging
from django.core.files.storage import Storage
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.exceptions import RefreshError, DefaultCredentialsError
from google.api_core.exceptions import NotFound, ServiceUnavailable
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)

class GoogleCloudMediaStorage(Storage):
    _client = None
    _bucket = None
    _initialized = False
    
    def __init__(self):
        # Use lazy initialization
        if not GoogleCloudMediaStorage._initialized:
            self._initialize_storage()
    
    def _initialize_storage(self):
        try:
            # Validate environment variables
            if "GCS_CREDENTIALS_JSON" not in os.environ:
                raise ValueError("GCS_CREDENTIALS_JSON environment variable not set")
            if "GS_BUCKET_NAME" not in os.environ:
                raise ValueError("GS_BUCKET_NAME environment variable not set")
                
            credentials_info = json.loads(os.environ["GCS_CREDENTIALS_JSON"])
            bucket_name = os.environ["GS_BUCKET_NAME"]
            
            # Retry mechanism for credential initialization
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Create credentials with explicit scopes
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_info,
                        scopes=["https://www.googleapis.com/auth/devstorage.full_control"]
                    )
                    
                    # Create client with explicit project ID
                    GoogleCloudMediaStorage._client = storage.Client(
                        credentials=credentials,
                        project=credentials_info.get('project_id')
                    )
                    GoogleCloudMediaStorage._bucket = GoogleCloudMediaStorage._client.bucket(bucket_name)
                    
                    # Verify bucket accessibility
                    if not GoogleCloudMediaStorage._bucket.exists():
                        raise ServiceUnavailable(f"Bucket {bucket_name} does not exist or is inaccessible")
                    
                    logger.info(f"Successfully connected to GCS bucket: {bucket_name}")
                    GoogleCloudMediaStorage._initialized = True
                    return
                    
                except (ServiceUnavailable, DefaultCredentialsError) as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Storage initialization failed (attempt {attempt+1}), retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise
                        
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid credentials configuration: {str(e)}")
            raise ValueError("Invalid GCS credentials configuration") from e
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            raise ServiceUnavailable(f"Storage service unavailable: {str(e)}") from e

    def _get_bucket(self):
        if not GoogleCloudMediaStorage._initialized:
            self._initialize_storage()
        return GoogleCloudMediaStorage._bucket

    def _save(self, name, content):
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(name)
            blob.upload_from_file(
                content,
                content_type=content.content_type,
                timeout=300
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
            bucket = self._get_bucket()
            return bucket.blob(name).exists()
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"GCS existence check error: {str(e)}")
            raise ServiceUnavailable("Storage service unavailable") from e

    def url(self, name):
        bucket = self._get_bucket()
        return f"https://storage.googleapis.com/{bucket.name}/{name}"

    def delete(self, name):
        try:
            bucket = self._get_bucket()
            bucket.blob(name).delete()
        except Exception as e:
            logger.error(f"GCS delete error: {str(e)}")
            raise e

    def size(self, name):
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(name)
            blob.reload()
            return blob.size
        except Exception as e:
            logger.error(f"GCS size check error: {str(e)}")
            raise e

    def get_modified_time(self, name):
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(name)
            blob.reload()
            return blob.updated
        except Exception as e:
            logger.error(f"GCS modified time check error: {str(e)}")
            raise e

    def path(self, name):
        raise NotImplementedError("Cloud storage doesn't support local paths")

    def open(self, name, mode='rb'):
        raise NotImplementedError("Cloud storage doesn't support direct file opening")
