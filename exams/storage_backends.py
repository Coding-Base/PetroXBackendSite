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
import jwt
import requests
import socket
import struct

logger = logging.getLogger(__name__)

# Constants for NTP time synchronization
NTP_SERVER = "pool.ntp.org"
NTP_PORT = 123
NTP_DELTA = 2208988800  # 1970-01-01 00:00:00 in NTP seconds

class GoogleCloudMediaStorage(Storage):
    _client = None
    _bucket = None
    _initialized = False
    
    def __init__(self):
        # Use lazy initialization - no heavy operations in constructor
        pass
    
    def deconstruct(self):
        """
        Required for Django migrations to serialize the storage class
        """
        return (
            'exams.storage_backends.GoogleCloudMediaStorage',
            [],
            {}
        )
    
    def _initialize_storage(self):
        """Initialize GCS connection with robust error handling and validation"""
        if GoogleCloudMediaStorage._initialized:
            return
            
        try:
            # 1. Verify environment variables exist
            if "GCS_CREDENTIALS_JSON" not in os.environ:
                raise ValueError("GCS_CREDENTIALS_JSON environment variable not set")
            if "GS_BUCKET_NAME" not in os.environ:
                raise ValueError("GS_BUCKET_NAME environment variable not set")
            
            credentials_json = os.environ["GCS_CREDENTIALS_JSON"]
            bucket_name = os.environ["GS_BUCKET_NAME"]
            
            # 2. Validate JSON format
            try:
                credentials_info = json.loads(credentials_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in credentials: {str(e)}")
                raise ValueError("Invalid JSON format in GCS_CREDENTIALS_JSON") from e
            
            # 3. Verify required credential fields
            required_keys = ["type", "project_id", "private_key_id", "private_key", "client_email"]
            for key in required_keys:
                if key not in credentials_info:
                    logger.error(f"Missing required key in credentials: {key}")
                    raise ValueError(f"Missing required key in credentials: {key}")
            
            # 4. Validate private key format
            private_key = credentials_info["private_key"]
            if not private_key.startswith("-----BEGIN PRIVATE KEY-----") or \
               not private_key.endswith("-----END PRIVATE KEY-----"):
                logger.error("Private key is not in PEM format")
                raise ValueError("Private key must be in PEM format")
            
            # 5. Verify system time is synchronized (critical for JWT)
            self._check_time_synchronization()
            
            # 6. Test JWT signature creation
            self._test_jwt_signature(credentials_info)
            
            # 7. Create credentials with retry
            credentials = self._create_credentials_with_retry(credentials_info)
            
            # 8. Initialize client and verify bucket
            GoogleCloudMediaStorage._client = storage.Client(
                credentials=credentials,
                project=credentials_info.get('project_id')
            )
            GoogleCloudMediaStorage._bucket = GoogleCloudMediaStorage._client.bucket(bucket_name)
            
            if not GoogleCloudMediaStorage._bucket.exists():
                raise ServiceUnavailable(f"Bucket {bucket_name} does not exist or is inaccessible")
            
            logger.info(f"Successfully connected to GCS bucket: {bucket_name}")
            GoogleCloudMediaStorage._initialized = True
            
        except Exception as e:
            logger.error(f"Storage initialization error: {str(e)}")
            raise ServiceUnavailable(f"Storage service unavailable: {str(e)}") from e

    def _check_time_synchronization(self):
        """Verify system time is synchronized with NTP server"""
        try:
            # Get NTP time
            ntp_time = self._get_ntp_time()
            system_time = datetime.now(timezone.utc)
            
            # Calculate time difference
            time_diff = (system_time - ntp_time).total_seconds()
            logger.info(f"System time: {system_time}, NTP time: {ntp_time}, Difference: {time_diff:.2f} seconds")
            
            # Warn if difference is significant
            if abs(time_diff) > 30:  # 30 seconds threshold
                logger.warning(f"System time is out of sync by {time_diff:.2f} seconds. JWT may fail!")
        except Exception as e:
            logger.error(f"Time synchronization check failed: {str(e)}")

    def _get_ntp_time(self):
        """Get current time from NTP server"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(5)
            data = b'\x1b' + 47 * b'\0'
            client.sendto(data, (NTP_SERVER, NTP_PORT))
            data, _ = client.recvfrom(1024)
            
            if data:
                t = struct.unpack('!12I', data)[10]
                t -= NTP_DELTA
                return datetime.utcfromtimestamp(t).replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.error(f"NTP request failed: {str(e)}")
            raise ServiceUnavailable("NTP time synchronization failed") from e
        
        raise ServiceUnavailable("Could not retrieve NTP time")

    def _test_jwt_signature(self, credentials_info):
        """Test JWT signature creation with the private key"""
        try:
            test_jwt = jwt.encode(
                {"test": "payload", "iat": int(time.time())},
                credentials_info["private_key"],
                algorithm="RS256",
                headers={"kid": credentials_info["private_key_id"]}
            )
            logger.debug("JWT test encoding successful")
            return True
        except jwt.PyJWTError as e:
            logger.error(f"JWT encoding test failed: {str(e)}")
            raise ValueError("Invalid private key format") from e
        except Exception as e:
            logger.error(f"Unexpected JWT test error: {str(e)}")
            raise

    def _create_credentials_with_retry(self, credentials_info, max_retries=3):
        """Create credentials with exponential backoff"""
        for attempt in range(max_retries):
            try:
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=["https://www.googleapis.com/auth/devstorage.full_control"]
                )
                
                # Test credentials by refreshing token
                request = requests.Request()
                credentials.refresh(request)
                logger.info("Google authentication test successful")
                return credentials
            except (ServiceUnavailable, DefaultCredentialsError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Authentication failed (attempt {attempt+1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Google authentication failed after {max_retries} attempts")
                    raise ServiceUnavailable("Google authentication failed") from e
            except Exception as e:
                logger.error(f"Unexpected authentication error: {str(e)}")
                raise

    def _get_bucket(self):
        """Get bucket instance with lazy initialization"""
        if not GoogleCloudMediaStorage._initialized:
            self._initialize_storage()
        return GoogleCloudMediaStorage._bucket

    def _save(self, name, content):
        """Save file to GCS with robust error handling"""
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(name)
            
            # Upload with increased timeout
            blob.upload_from_file(
                content,
                content_type=content.content_type,
                timeout=300  # 5 minutes
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
