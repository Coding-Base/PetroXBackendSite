# exams/storage_backends.py
import os
import json
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.cloud import storage
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound, Forbidden, ServiceUnavailable
from google.auth.exceptions import RefreshError

logger = logging.getLogger(__name__)

@deconstructible
class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        self.creds_value = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
        self._client = None
        self._bucket = None
        
        if not self.creds_value:
            raise ImproperlyConfigured(
                "GOOGLE_APPLICATION_CREDENTIALS setting is not configured"
            )

    @property
    def client(self):
        if self._client is None:
            self._client = storage.Client(credentials=self._get_credentials())
        return self._client

    @property
    def bucket(self):
        if self._bucket is None:
            bucket_name = getattr(settings, 'GS_BUCKET_NAME', 'petrox-materials')
            self._bucket = self.client.bucket(bucket_name)
        return self._bucket

    def _get_credentials(self):
        try:
            # Try parsing as JSON credentials
            creds_json = json.loads(self.creds_value)
            return service_account.Credentials.from_service_account_info(creds_json)
        except json.JSONDecodeError:
            # Fall back to file path
            if os.path.exists(self.creds_value):
                return service_account.Credentials.from_service_account_file(self.creds_value)
            raise ImproperlyConfigured(
                f"GCS credentials not found at: {self.creds_value} and not valid JSON"
            )

    def _save(self, name, content):
        try:
            blob = self.bucket.blob(name)
            blob.upload_from_file(
                content,
                content_type=content.content_type,
                timeout=300
            )
            return name
        except Forbidden as e:
            logger.error(f"GCS Permission error: {str(e)}")
            raise PermissionError("Insufficient permissions to upload to GCS") from e
        except NotFound as e:
            logger.error(f"GCS Bucket not found: {str(e)}")
            raise RuntimeError("GCS Bucket not found") from e
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
            blob = self.bucket.blob(name)
            return blob.exists()
        except NotFound:
            return False

    def url(self, name):
        return f"https://storage.googleapis.com/{self.bucket.name}/{name}"
