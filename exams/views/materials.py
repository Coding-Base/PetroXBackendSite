# exams/views/materials.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from django.conf import settings
from django.db import models
import logging
import cloudinary.uploader

from ..models import Material
from ..serializers import MaterialSerializer
from .. import cloudinary_utils as cloud_utils  # module: exams/cloudinary_utils.py

logger = logging.getLogger(__name__)


class MaterialUploadView(CreateAPIView):
    """
    Accepts multipart/form-data with a 'file' field and uploads the file to Cloudinary
    as a public raw resource. Saves the returned URL into Material.file (URLField).
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "No file provided"})

        # Default max upload bytes. Adjust to your Cloudinary plan (10MB by default).
        max_bytes = int(getattr(settings, "MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
        if uploaded_file.size > max_bytes:
            raise ValidationError({"file": f"File size exceeds limit ({max_bytes} bytes)."})

        try:
            # Upload as a raw resource and make it public (type="upload")
            upload_result = cloudinary.uploader.upload(
                uploaded_file,
                resource_type="raw",  # required for pdf/doc
                folder="materials",
                type="upload",        # public (not authenticated)
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        except Exception as exc:
            logger.exception("Cloudinary upload failed")
            # Return a generic API error; the frontend can show the message
            raise APIException({"detail": "Storage upload failed", "error": str(exc)})

        # Prefer secure_url, fallback to url
        file_url = upload_result.get("secure_url") or upload_result.get("url")
        if not file_url:
            logger.error("Cloudinary upload returned no URL: %s", upload_result)
            raise APIException("Upload succeeded but storage returned no URL")

        # Save the material instance with the returned URL
        serializer.save(uploaded_by=self.request.user, file=file_url)


class MaterialDownloadView(RetrieveAPIView):
    """
    Returns JSON: { "download_url": "<public or signed url>" } for the material.
    The frontend should open that URL to download/view the file.
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = cloud_utils.get_cloudinary_signed_or_public_url(material)
        except Exception:
            logger.exception("Error generating download URL for material id=%s", getattr(material, "id", None))
            return Response({"detail": "Failed to generate download URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not download_url:
            return Response({"detail": "No download URL available"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"download_url": download_url}, status=status.HTTP_200_OK)


class MaterialSearchView(ListAPIView):
    """
    Search materials by name, tags, or course name.
    Expects query parameter: ?query=...
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("query", "").strip()
        if not query:
            return Material.objects.none()

        return Material.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(tags__icontains=query) |
            models.Q(course__name__icontains=query)
        )
