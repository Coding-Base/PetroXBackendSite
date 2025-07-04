# exams/storage_backends.py
import os
import json
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from google.cloud import storage
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound


@deconstructible
class GoogleCloudMediaStorage(Storage):
    def __init__(self):
        credentials_info = json.loads(os.environ["GCS_CREDENTIALS_JSON"])
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        self.client = storage.Client(
            credentials=credentials,
            project=os.environ.get("GS_PROJECT_ID")
        )
        self.bucket = self.client.bucket(os.environ.get("GS_BUCKET_NAME"))

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
            return self.bucket.blob(name).exists()
        except NotFound:
            return False

    def url(self, name):
        return f"https://storage.googleapis.com/{self.bucket.name}/{name}"
