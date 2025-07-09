# storage_backends.py
# exams/storage_backends.py
from django.conf import settings
from google.cloud import storage
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound
import os

@deconstructible
class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        creds_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        self.client = storage.Client(credentials=credentials)
        self.bucket = self.client.bucket(settings.GS_BUCKET_NAME)
    
    def _save(self, name, content):
        blob = self.bucket.blob(name)
        
        # Disable ACLs and use IAM policies
        blob.upload_from_file(
            content,
            content_type=content.content_type,
            # Prevent ACL-related operations
            predefined_acl=None,
            if_generation_match=None
        )
        return name
    
    def exists(self, name):
        try:
            return self.bucket.blob(name).exists()
        except NotFound:
            return False
    
    def url(self, name):
        # Direct public URL format
        return f"https://storage.googleapis.com/{self.bucket.name}/{name}"
