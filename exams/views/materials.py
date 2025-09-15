# exams/views/materials.py
import logging

from django.conf import settings
from django.db import DataError, IntegrityError, transaction
from django.utils import timezone

import cloudinary.uploader
from rest_framework import generics, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from ..models import Material
from ..serializers import MaterialSerializer
from exams.cloudinary_utils import get_cloudinary_signed_or_public_url

logger = logging.getLogger(__name__)


def _truncate_field_if_needed(model_class, field_name, value):
    """
    Helper to truncate a string value to the model field's max_length.
    Returns the possibly-truncated value and a boolean indicating whether truncation occurred.
    """
    if value is None:
        return value, False

    try:
        field = model_class._meta.get_field(field_name)
        max_len = getattr(field, "max_length", None)
        if max_len and isinstance(value, str) and len(value) > max_len:
            return value[:max_len], True
    except Exception:
        # If anything goes wrong, just return the original value and don't truncate.
        return value, False

    return value, False


class MaterialUploadView(generics.CreateAPIView):
    """
    Upload a material (multipart/form-data expected).
    File is uploaded to Cloudinary as a public 'raw' resource and the secure_url is saved
    in the Material.file URLField.
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        request = self.request

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "No file provided"})

        # Optional: enforce server-side file size limit (in bytes)
        max_file_size_bytes = int(getattr(settings, "MATERIAL_MAX_FILE_SIZE", 20 * 1024 * 1024))
        if uploaded_file.size > max_file_size_bytes:
            raise ValidationError({"file": f"File too large. Maximum allowed is {max_file_size_bytes} bytes."})

        # Upload to Cloudinary (public raw)
        try:
            upload_result = cloudinary.uploader.upload(
                uploaded_file,
                resource_type="raw",   # raw to preserve PDFs/docs
                folder="materials",
                type="upload",         # ensure public (not authenticated/signed)
                use_filename=True,
                unique_filename=True,  # avoid collisions
                timeout=120  # seconds - adjust if you need larger timeouts
            )
            logger.debug("Cloudinary upload result: %s", upload_result)
        except Exception as exc:
            logger.exception("Cloudinary upload failed")
            raise APIException(detail=f"Failed to upload file to storage: {str(exc)}")

        file_url = upload_result.get("secure_url") or upload_result.get("url")
        if not file_url:
            logger.error("No URL returned from Cloudinary upload_result=%s", upload_result)
            raise APIException(detail="Upload succeeded but no file URL was returned by storage provider.")

        # Defensive truncation to match DB field lengths (avoids DataError)
        # We inspect serializer.validated_data here for fields that map to model columns.
        validated = serializer.validated_data.copy()

        # Truncate 'name' and 'tags' if they exceed DB column lengths
        if "name" in validated:
            truncated_name, truncated = _truncate_field_if_needed(Material, "name", validated["name"])
            if truncated:
                logger.warning("Truncated material name to fit DB column length.")
                validated["name"] = truncated_name

        if "tags" in validated:
            truncated_tags, truncated = _truncate_field_if_needed(Material, "tags", validated.get("tags"))
            if truncated:
                logger.warning("Truncated material tags to fit DB column length.")
                validated["tags"] = truncated_tags

        # Save in a transaction to get atomic behavior
        try:
            with transaction.atomic():
                # serializer.save accepts overrides; pass file and uploaded_by explicitly
                serializer.save(
                    uploaded_by=request.user,
                    file=file_url,
                    **validated
                )
        except DataError as e:
            # Database-level data issues (e.g., string too long)
            logger.exception("Database DataError while saving Material: %s", e)
            raise APIException(detail=f"Database error saving material: {str(e)}")
        except IntegrityError as e:
            logger.exception("Database IntegrityError while saving Material: %s", e)
            raise APIException(detail=f"Database integrity error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error saving material: %s", e)
            raise APIException(detail="Failed to save material")


class MaterialDownloadView(RetrieveAPIView):
    """
    Return a download URL for the given material id.
    Prefer generating a signed URL (if needed) via get_cloudinary_signed_or_public_url,
    otherwise fall back to the saved file URL string.
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()

        # material.file may already be a URL string (we store secure_url)
        file_value = getattr(material, "file", None)

        # Try cloudinary helper which may accept either a Material instance or a string.
        try:
            # call helper defensively - it should accept either a string or object; if not, handle fallback below
            download_url = get_cloudinary_signed_or_public_url(file_value)
        except Exception as e:
            logger.warning("get_cloudinary_signed_or_public_url failed: %s; falling back to stored URL", e)
            # If the helper failed but the saved value is a valid URL string, use it
            if isinstance(file_value, str) and (file_value.startswith("http://") or file_value.startswith("https://") or file_value.startswith("//")):
                download_url = file_value
            else:
                logger.exception("Failed to generate download URL for Material id=%s", getattr(material, "id", "<unknown>"))
                raise APIException(detail="Failed to generate download URL")

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
