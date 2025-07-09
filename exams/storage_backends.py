# exams/storage_backends.py
import os
import json
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.cloud import storage
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound

@deconstructible
class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        # Store credentials value but don't process it yet
        self.creds_value = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
        self._client = None
        self._bucket = None
        
        if not self.creds_value:
            raise ImproperlyConfigured(
                "GOOGLE_APPLICATION_CREDENTIALS setting is not configured"
            )

    @property
    def client(self):
        """Lazy-loaded GCS client"""
        if self._client is None:
            self._client = storage.Client(credentials=self._get_credentials())
        return self._client

    @property
    def bucket(self):
        """Lazy-loaded GCS bucket"""
        if self._bucket is None:
            bucket_name = getattr(settings, 'GS_BUCKET_NAME', 'petrox-materials')
            self._bucket = self.client.bucket(bucket_name)
        return self._bucket

    def _get_credentials(self):
        """Handle both file paths and JSON credential strings"""
        try:
            # First try to parse as JSON
            creds_json = json.loads(self.creds_value)
            return service_account.Credentials.from_service_account_info(creds_json)
        except json.JSONDecodeError:
            # If not JSON, treat as file path
            if os.path.exists(self.creds_value):
                return service_account.Credentials.from_service_account_file(self.creds_value)
            raise ImproperlyConfigured(
                f"GCS credentials not found at: {self.creds_value} and not valid JSON"
            )

    def _save(self, name, content):
        blob = self.bucket.blob(name)
        blob.upload_from_file(
            content,
            content_type=content.content_type,
            predefined_acl=None,
            if_generation_match=None
        )
        return name

    def exists(self, name):
        try:
            blob = self.bucket.blob(name)
            return blob.exists()
        except NotFound:
            return False

    def url(self, name):
        return f"https://storage.googleapis.com/{self.bucket.name}/{name}"
