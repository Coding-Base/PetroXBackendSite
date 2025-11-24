# exams/cloudinary_utils.py
import os
import logging
import urllib.parse
from django.conf import settings

try:
    import cloudinary
    import cloudinary.utils
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_cloudinary_signed_or_public_url(material, expires_in=3600):
    """
    Return a download URL for the given Material instance.
    If Cloudinary resources are restricted (e.g., admin-only access),
    generates a signed URL. Otherwise returns a public URL.
    
    Accepts Material.file as either:
      - absolute URL string (https://...)
      - relative path string (media/... or media/media/...)
      - FieldFile-like object (has .url or .name)
    
    Args:
        material: Material instance or file value (string/FieldFile)
        expires_in: Signed URL expiration time in seconds (default 1 hour)
    
    Returns:
        A working download URL (public or signed based on resource restrictions)
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

    # If already an absolute URL, try to use it; if it's a signed URL already, return it
    if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
        # If it's already a Cloudinary URL with 's_' (signed), return as-is
        if 's_' in url or 'signature' in url.lower():
            return url
        # Otherwise, attempt to sign it if it's from Cloudinary
        if 'cloudinary.com' in url and CLOUDINARY_AVAILABLE:
            try:
                return _sign_cloudinary_url(url, expires_in)
            except Exception as e:
                logger.warning(f"Failed to sign Cloudinary URL: {e}; returning original URL")
                return url
        return url

    # It's a relative path — extract public_id and generate signed URL
    # remove leading slashes and "media/" prefix if present
    cleaned = url.lstrip("/")
    cleaned = cleaned.replace("media/", "").replace("media/media/", "")

    cloud_name = None
    cfg = getattr(settings, "CLOUDINARY_STORAGE", None)
    if cfg and isinstance(cfg, dict):
        cloud_name = cfg.get("CLOUD_NAME")
    if not cloud_name:
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUD_NAME")

    if not cloud_name:
        logger.warning("CLOUDINARY_CLOUD_NAME not configured; cannot generate URL")
        return ""

    # Try to generate a signed URL for restricted resources
    if CLOUDINARY_AVAILABLE:
        try:
            signed_url = _generate_signed_url(cleaned, cloud_name, expires_in)
            if signed_url:
                return signed_url
        except Exception as e:
            logger.warning(f"Failed to generate signed URL for {cleaned}: {e}")

    # Fallback: return public URL (works if resources are public)
    encoded = urllib.parse.quote(cleaned, safe="/")
    public_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{encoded}"
    return public_url


def _generate_signed_url(public_id, cloud_name, expires_in=3600):
    """
    Generate a signed Cloudinary URL for a raw (document/file) resource.
    Required if the Cloudinary folder has restricted access (e.g., admin-only).
    
    Args:
        public_id: The Cloudinary public_id (e.g., 'materials/file.pdf')
        cloud_name: The Cloudinary cloud name
        expires_in: Expiration time in seconds
    
    Returns:
        Signed URL string or None if signing fails
    """
    if not CLOUDINARY_AVAILABLE:
        logger.warning("Cloudinary SDK not available; cannot generate signed URL")
        return None

    try:
        # Ensure cloudinary is configured with credentials
        if not cloudinary.config().api_secret:
            logger.warning(
                "⚠️  CLOUDINARY_API_SECRET not configured! "
                "Signed URLs cannot be generated for restricted resources. "
                "Set CLOUDINARY_API_SECRET in environment variables or change Cloudinary folder to public access."
            )
            return None

        # Generate a signed URL for the raw resource
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type='raw',
            type='private',  # 'private' requires signature for download
            sign_url=True,
            secure=True,
            expires_in=expires_in,
        )
        logger.debug(f"✓ Generated signed URL for {public_id} (expires in {expires_in}s)")
        return url
    except Exception as e:
        logger.error(f"❌ Error generating signed URL for {public_id}: {e}")
        return None


def _sign_cloudinary_url(url, expires_in=3600):
    """
    Re-sign an existing Cloudinary URL if it's not already signed.
    Useful if you have a plain public URL but need it signed for restricted resources.
    
    Args:
        url: The Cloudinary URL (either public or already signed)
        expires_in: Expiration time in seconds
    
    Returns:
        Signed URL or original URL if re-signing fails
    """
    if not CLOUDINARY_AVAILABLE or not cloudinary.config().api_secret:
        return url

    try:
        # Extract public_id from URL (rough heuristic for raw uploads)
        # URL format: https://res.cloudinary.com/CLOUD_NAME/raw/upload/VERSION/materials/file.pdf
        parts = url.split('/upload/')
        if len(parts) < 2:
            return url

        path_part = parts[1]  # e.g., "v1234/materials/file.pdf"
        # Remove version prefix if present
        if '/' in path_part:
            public_id = '/'.join(path_part.split('/')[1:])
        else:
            public_id = path_part

        return _generate_signed_url(public_id, cloudinary.config().cloud_name, expires_in) or url
    except Exception as e:
        logger.warning(f"Failed to re-sign URL: {e}")
        return url
