# exams/views/materials.py
import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

import cloudinary.uploader

from ..models import Material
from ..serializers import MaterialSerializer
from ..cloudinary_utils import get_cloudinary_signed_or_public_url

logger = logging.getLogger(__name__)


class MaterialUploadView(CreateAPIView):
    """
    POST /api/materials/upload/
    Accepts multipart/form-data with a field 'file' (actual file) and other fields:
      - course (id)
      - name
      - tags (optional)
    Behavior:
      - Accepts the incoming file from request.FILES['file'] (requires multipart form).
      - Uploads the file to Cloudinary as raw/public.
      - Uses the returned secure URL in place of the file when validating the serializer,
        so the Material.file (URLField) always receives a valid URL.
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # ensure DRF reads request.FILES

    def create(self, request, *args, **kwargs):
        # Ensure the incoming request actually included a file in request.FILES
        incoming_file = request.FILES.get("file")
        if not incoming_file:
            # This is the error you were seeing on the frontend; return descriptive message
            return Response({"file": ["No file provided"]}, status=status.HTTP_400_BAD_REQUEST)

        # Server-side size limit (optional override via settings)
        max_bytes = int(getattr(settings, "MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
        if incoming_file.size > max_bytes:
            return Response(
                {"file": [f"File too large. Maximum size allowed is {max_bytes} bytes."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upload to Cloudinary (raw resource, public)
        try:
            upload_result = cloudinary.uploader.upload(
                incoming_file,
                resource_type="raw",    # necessary for pdf/doc/raw files
                folder="materials",
                type="upload",          # public upload (not authenticated)
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        except Exception as exc:
            logger.exception("Cloudinary upload failed: %s", exc)
            return Response(
                {"file": [f"Storage upload failed: {str(exc)}"]},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Prefer secure_url if available, fallback to url
        file_url = upload_result.get("secure_url") or upload_result.get("url")
        if not file_url:
            logger.error("Cloudinary returned no URL for uploaded file: %s", upload_result)
            return Response(
                {"file": ["Upload succeeded but storage returned no URL."]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Replace 'file' in the serializer data with the URL we got from Cloudinary.
        # request.data may be a QueryDict; copy it to mutate safely.
        data = request.data.copy()
        data["file"] = file_url

        # Validate serializer now that file is a URL (Material.file is a URLField)
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as ve:
            logger.warning("Serializer validation failed after successful upload: %s", ve)
            # (Optional) You can delete the uploaded Cloudinary resource here if you want to clean up.
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Unexpected error validating serializer after upload")
            return Response({"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # Save the instance, attaching uploaded_by
        try:
            instance = serializer.save(uploaded_by=request.user)
        except Exception as exc:
            logger.exception("Failed to save Material instance after upload: %s", exc)
            return Response({"detail": "Failed to save material"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return created serializer data
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MaterialDownloadView(RetrieveAPIView):
    """
    GET /api/materials/download/<id>/
    Returns JSON: {"download_url": "<public_or_signed_url>"}
    Frontend should use this URL to trigger downloads (open link/new tab or anchor click).
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = get_cloudinary_signed_or_public_url(material)
        except Exception as exc:
            logger.exception(
                "Error generating download URL for material id=%s: %s",
                getattr(material, "id", None),
                exc,
            )
            return Response({"detail": "Failed to generate download URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not download_url:
            return Response({"detail": "No download URL available"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"download_url": download_url}, status=status.HTTP_200_OK)


class MaterialSearchView(ListAPIView):
    """
    GET /api/materials/search/?query=...
    Returns matching materials (MaterialSerializer).
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = self.request.query_params.get("query", "").strip()
        if not q:
            return Material.objects.none()
        return Material.objects.filter(
            models.Q(name__icontains=q) |
            models.Q(tags__icontains=q) |
            models.Q(course__name__icontains=q)
        )
