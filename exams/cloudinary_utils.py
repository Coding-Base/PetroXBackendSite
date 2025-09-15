# exams/cloudinary_utils.py
import os
import logging
import urllib.parse
from django.conf import settings

logger = logging.getLogger(__name__)

def get_cloudinary_signed_or_public_url(material):
    """
    Return a usable public download URL for the given Material instance.
    Accepts Material.file as either:
      - absolute URL string (https://...)
      - relative path string (media/... or media/media/...)
      - FieldFile-like object (has .url or .name)
    If CLOUDINARY_CLOUD_NAME is configured, construct a res.cloudinary.com/raw/upload/<path> URL
    for relative paths so downloads are public.
    """
    f = getattr(material, "file", None)
    if not f:
        return ""

    # If FieldFile-like: prefer .url then .name
    url = None
    try:
        if hasattr(f, "url"):
            url = f.url
    except Exception:
        # accessing FieldFile.url may raise if storage needs credentials — fallback below
        url = None

    if not url:
        # If f is a string, use it
        if isinstance(f, str):
            url = f
        else:
            # try name attribute (FieldFile.name)
            name = getattr(f, "name", None)
            if name:
                url = name

    if not url:
        return ""

    url = str(url).strip()

    # If already an absolute URL, return it (assume public)
    if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
        return url

    # It's a relative path — try to construct a public Cloudinary URL:
    # remove leading slashes and "media/" prefix if present
    cleaned = url.lstrip("/")
    cleaned = cleaned.replace("media/", "").replace("media/media/", "")

    cloud_name = None
    cfg = getattr(settings, "CLOUDINARY_STORAGE", None)
    if cfg and isinstance(cfg, dict):
        cloud_name = cfg.get("CLOUD_NAME")
    if not cloud_name:
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUD_NAME")

    if cloud_name:
        # Cloudinary requires proper URL-encoding for filenames/paths
        encoded = urllib.parse.quote(cleaned, safe="/")
        public_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{encoded}"
        return public_url

    # Fallback to MEDIA_URL + cleaned (may be non-public)
    media_url = getattr(settings, "MEDIA_URL", "")
    if media_url and not cleaned.startswith("http"):
        return media_url.rstrip("/") + "/" + cleaned.lstrip("/")

    # Last resort, return cleaned path
    return cleaned
