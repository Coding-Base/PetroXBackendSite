# exams/storage_backends.py
from django.conf import settings
from google.cloud import storage
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound
from django.core.exceptions import ImproperlyConfigured
import os

@deconstructible
class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        # Lazy initialization - don't access settings here
        self._client = None
        self._bucket = None

    @property
    def client(self):
        """Lazy-loaded GCS client"""
        if self._client is None:
            creds_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            
            if not creds_path:
                raise ImproperlyConfigured(
                    "GOOGLE_APPLICATION_CREDENTIALS setting is not configured"
                )
            
            if not os.path.exists(creds_path):
                raise ImproperlyConfigured(
                    f"GCS credentials file not found at: {creds_path}"
                )
                
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            self._client = storage.Client(credentials=credentials)
        return self._client

    @property
    def bucket(self):
        """Lazy-loaded GCS bucket"""
        if self._bucket is None:
            bucket_name = getattr(settings, 'GS_BUCKET_NAME', 'petrox-materials')
            self._bucket = self.client.bucket(bucket_name)
        return self._bucket

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
