# exams/views/materials.py
from rest_framework import status, generics
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
from ..cloudinary_utils import get_cloudinary_signed_or_public_url

logger = logging.getLogger(__name__)


class MaterialUploadView(CreateAPIView):
    """
    Endpoint: POST /api/materials/upload/
    Accepts multipart/form-data with 'file' (actual file) and other fields.
    We upload the file to Cloudinary first (as public raw), then validate serializer
    with the returned URL so Material.file (URLField) receives a URL (no "Enter a valid URL." error).
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Expect a file in request.FILES (multipart/form-data)
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"file": ["No file provided"]}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce server-side file size limits (default 10MB unless overridden in settings)
        max_bytes = int(getattr(settings, "MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
        if uploaded_file.size > max_bytes:
            return Response(
                {"file": [f"File size exceeds limit ({max_bytes} bytes)."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Upload to Cloudinary as raw (public)
        try:
            upload_result = cloudinary.uploader.upload(
                uploaded_file,
                resource_type="raw",    # needed for pdf/doc
                folder="materials",
                type="upload",          # public (not authenticated)
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                # optionally set timeout or other options here
            )
        except Exception as exc:
            logger.exception("Cloudinary upload failed: %s", exc)
            # Return response shape similar to serializer errors for frontend handling
            return Response(
                {"file": [f"Storage upload failed: {str(exc)}"]},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Prefer secure_url
        file_url = upload_result.get("secure_url") or upload_result.get("url")
        if not file_url:
            logger.error("Cloudinary upload returned no URL: %s", upload_result)
            return Response(
                {"file": ["Upload succeeded but storage returned no URL."]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Build payload for serializer validation: copy request.data and replace file with the URL
        # request.data is usually a QueryDict (immutable-ish), so copy()
        data = request.data.copy()
        data["file"] = file_url

        # Validate serializer with the URL (so 'file' passes URLField validation)
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            # If validation fails (e.g., missing required fields), attempt to delete the uploaded file
            # (optional cleanup; you may want to remove the uploaded Cloudinary resource)
            logger.warning("Serializer validation failed after upload: %s", ve)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Unexpected serializer validation error")
            return Response({"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # Save instance with uploaded_by
        try:
            instance = serializer.save(uploaded_by=request.user)
        except Exception as exc:
            logger.exception("Failed to save Material instance after upload: %s", exc)
            return Response({"detail": "Failed to save material"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return serialized created object
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MaterialDownloadView(RetrieveAPIView):
    """
    Endpoint: GET /api/materials/download/<id>/
    Returns JSON: { "download_url": "<public_or_signed_url>" }
    Frontend should use this URL for download (open in new tab or create anchor).
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = get_cloudinary_signed_or_public_url(material)
        except Exception as exc:
            logger.exception("Error generating download URL for material id=%s: %s", getattr(material, "id", None), exc)
            return Response({"detail": "Failed to generate download URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not download_url:
            return Response({"detail": "No download URL available"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"download_url": download_url}, status=status.HTTP_200_OK)


class MaterialSearchView(ListAPIView):
    """
    Endpoint: GET /api/materials/search/?query=...
    Returns list of Material (uses MaterialSerializer).
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
