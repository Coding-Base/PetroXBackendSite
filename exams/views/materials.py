# exams/views/materials.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import RetrieveAPIView
from django.conf import settings
import logging
import cloudinary.uploader

from ..models import Material
from ..serializers import MaterialSerializer
from .. import cloudinary_utils as cloud_utils  # correct relative import (module lives at exams/cloudinary_utils.py)

logger = logging.getLogger(__name__)


class MaterialUploadView(generics.CreateAPIView):
    """
    Uploads an incoming file to Cloudinary (raw resource) with public type,
    then saves the returned secure_url into the Material.file URL field.
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "No file provided"})

        # Optional: enforce a maximum file size server-side (match frontend limit)
        max_bytes = int(getattr(settings, "MAX_UPLOAD_BYTES", 20 * 1024 * 1024))  # default 20MB
        if uploaded_file.size > max_bytes:
            raise ValidationError({"file": f"File size exceeds limit ({max_bytes} bytes)."})

        try:
            # Upload to Cloudinary as a raw/public resource
            upload_result = cloudinary.uploader.upload(
                uploaded_file,
                resource_type="raw",  # required for pdf/doc
                folder="materials",
                type="upload",        # ensures public (not authenticated)
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                # you can control timeout or other options here if needed
            )
        except Exception as e:
            logger.exception("Cloudinary upload failed")
            # Wrap for DRF to return 500 with message
            raise APIException({"detail": "Storage upload failed", "error": str(e)})

        # Get a usable URL from upload result (secure_url preferred)
        file_url = upload_result.get("secure_url") or upload_result.get("url")
        if not file_url:
            logger.error("Cloudinary upload returned no URL: %s", upload_result)
            raise APIException("Upload succeeded but storage returned no URL")

        # Save the material with uploaded_by and file URL
        serializer.save(uploaded_by=self.request.user, file=file_url)


class MaterialDownloadView(RetrieveAPIView):
    """
    Returns a JSON with { "download_url": "<public or signed url>" } for the requested material id.
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = cloud_utils.get_cloudinary_signed_or_public_url(material)
        except Exception as e:
            logger.exception("Error generating download URL for material id=%s", getattr(material, "id", None))
            return Response({"detail": "Failed to generate download URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not download_url:
            return Response({"detail": "No download URL available"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"download_url": download_url}, status=status.HTTP_200_OK)
