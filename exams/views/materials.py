# exams/views/materials.py
import logging

from django.conf import settings
from django.db import DataError, IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

import cloudinary.uploader
from rest_framework import generics, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
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

        # Get the file from serializer validated data
        uploaded_file = serializer.validated_data.get("file")
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

        # Remove the file from validated_data as we'll use the URL instead
        validated_data = serializer.validated_data.copy()
        validated_data.pop('file', None)

        # Defensive truncation to match DB field lengths (avoids DataError)
        # Truncate 'name' and 'tags' if they exceed DB column lengths
        if "name" in validated_data:
            truncated_name, truncated = _truncate_field_if_needed(Material, "name", validated_data["name"])
            if truncated:
                logger.warning("Truncated material name to fit DB column length.")
                validated_data["name"] = truncated_name

        if "tags" in validated_data:
            truncated_tags, truncated = _truncate_field_if_needed(Material, "tags", validated_data.get("tags"))
            if truncated:
                logger.warning("Truncated material tags to fit DB column length.")
                validated_data["tags"] = truncated_tags

        # Save in a transaction to get atomic behavior
        try:
            with transaction.atomic():
                # serializer.save accepts overrides; pass file and uploaded_by explicitly
                serializer.save(
                    uploaded_by=request.user,
                    file=file_url,
                    **validated_data
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
    If Cloudinary resources are restricted (e.g., admin-only folder),
    returns a signed URL. Otherwise returns public URL.
    
    GET /api/materials/download/{id}/
    Response: { "download_url": "https://..." }
    """
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()

        # material.file is the Cloudinary URL string
        file_value = getattr(material, "file", None)

        try:
            # Generate signed URL (if needed) or fall back to public URL
            # URLs are valid for 1 hour by default
            download_url = get_cloudinary_signed_or_public_url(file_value, expires_in=3600)
        except Exception as e:
            logger.exception("Failed to generate download URL for Material id=%s", material.id)
            raise APIException(detail="Failed to generate download URL")

        if not download_url:
            logger.error("No download URL available for Material id=%s", material.id)
            raise APIException(detail="Failed to generate download URL")

        return Response({"download_url": download_url}, status=status.HTTP_200_OK)


class MaterialSearchView(ListAPIView):
    """
    GET /api/materials/search/?query=...
    Returns matching materials (MaterialSerializer).
    Searches by name, tags, or course name.
    """
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Accept either ?query=term or accidentally encoded ?query[query]=term
        raw_params = self.request.GET.dict()
        logger.debug("Raw search GET params: %s", raw_params)

        q = self.request.query_params.get("query")
        # fallback for malformed/wrapped param names like query[query]
        if not q:
            q = self.request.query_params.get('query[query]') or self.request.query_params.get('query%5Bquery%5D')

        q = (q or "").strip()
        logger.info(f"Material search initiated with query: '{q}'")

        if not q:
            logger.warning("Empty search query provided")
            return Material.objects.none()
        
        # Build the filter with Q objects
        queryset = Material.objects.filter(
            Q(name__icontains=q) |
            Q(tags__icontains=q) |
            Q(course__name__icontains=q)
        ).distinct()
        
        result_count = queryset.count()
        logger.info(f"Search returned {result_count} results for query '{q}'")
        
        return queryset


class MaterialListView(ListAPIView):
    """
    GET /api/materials/
    Returns all materials (paginated) for the authenticated user.
    Useful for browsing and testing.
    """
    queryset = Material.objects.all().order_by('-uploaded_at')
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
