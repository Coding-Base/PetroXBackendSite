# exams/cloudinary_utils.py
import os
import re
from django.conf import settings
from rest_framework.exceptions import APIException

try:
    import cloudinary
    import cloudinary.utils
except Exception:
    cloudinary = None  # ok — we'll still handle string URLs


def get_cloudinary_signed_or_public_url(material):
    """
    Given a Material instance, return a safe public URL for download.
    Handles:
      - material.file as an absolute URL string (preferred)
      - legacy FieldFile-like (has .url)
      - fallback: build a naive cloudinary raw upload URL if we can find the cloud name
    """
    f = getattr(material, "file", None)
    if not f:
        raise APIException("No file found for this material")

    # If it's a FieldFile-like object with .url, prefer that
    if hasattr(f, "url"):
        try:
            url = f.url
            if url:
                return url
        except Exception:
            # continue to next attempts
            pass

        # try to get a file name and fall back
        name = getattr(f, "name", None)
        if isinstance(name, str):
            f = name  # continue treating as string

    # If it's a plain string URL, return it directly if absolute
    if isinstance(f, str):
        if f.startswith("http://") or f.startswith("https://") or f.startswith("//"):
            return f

        # Otherwise try to build a Cloudinary raw upload public URL
        # Use cloud name from settings or env
        cloud_name = None
        # Try a few places for the cloud name
        c_cfg = getattr(settings, "CLOUDINARY", None)
        if c_cfg and isinstance(c_cfg, dict):
            cloud_name = c_cfg.get("cloud_name") or c_cfg.get("CLOUDINARY_CLOUD_NAME")
        if not cloud_name:
            cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUD_NAME") or os.environ.get("CLOUDINARY_CLOUDNAME")

        if not cloud_name:
            # If we can't construct a cloudinary URL, return a helpful error
            raise APIException("Material file is not an absolute URL and Cloudinary cloud name is not configured.")

        # sanitize and remove leading media/ or slashes
        public_path = f.lstrip("/").replace("media/", "").replace("media/media/", "")
        # If there is a version prefix like v123/ keep it — we don't attempt to invent one
        # Build a conservative public URL (raw/upload)
        # Note: Cloudinary sometimes requires the version segment; if the original secure_url had it, we would have returned that above.
        built = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{public_path}"
        return built

    # Not a string or url-like file
    raise APIException("Unable to determine download URL for the requested material")
