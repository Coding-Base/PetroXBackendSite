# exams/views/materials.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException, ValidationError
import logging
from ..models import Material
from ..serializers import MaterialSerializer
from . import cloudinary_utils as cloud_utils  # local import to avoid circular issues
from rest_framework.generics import RetrieveAPIView

import cloudinary.uploader
from django.conf import settings

logger = logging.getLogger(__name__)


class MaterialUploadView(generics.CreateAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "No file provided"})

        # enforce a maximum size before sending to Cloudinary (use settings or 10MB default)
        max_bytes = getattr(settings, "CLOUDINARY_MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
        if uploaded_file.size > max_bytes:
            raise ValidationError({"file": f"File too large. Max allowed {max_bytes} bytes."})

        try:
            # Upload to Cloudinary as raw (pdf/doc) and force public upload
            upload_result = cloudinary.uploader.upload(
                uploaded_file,
                resource_type="raw",
                folder="materials",
                type="upload"  # ensures public, not authenticated
            )
        except Exception as e:
            logger.exception("Cloudinary upload failed")
            raise APIException(f"Failed to upload file to storage: {str(e)}")

        # The upload_result should include 'secure_url' — save that URL into the model
        secure_url = upload_result.get("secure_url") or upload_result.get("url")
        if not secure_url:
            logger.error("Cloudinary returned no secure URL: %s", upload_result)
            raise APIException("Storage upload did not return a usable URL")

        # Save the object with the public URL
        serializer.save(
            uploaded_by=self.request.user,
            file=secure_url
        )


class MaterialDownloadView(RetrieveAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = cloud_utils.get_cloudinary_signed_or_public_url(material)
        except APIException as e:
            logger.exception("Error generating download URL")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Unexpected error generating download URL")
            return Response({"detail": "Failed to generate download URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"download_url": download_url})

