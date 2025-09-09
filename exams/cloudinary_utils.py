# exams/cloudinary_utils.py
import os
from urllib.parse import urlparse
import cloudinary
import cloudinary.api
from cloudinary.utils import cloudinary_url

def extract_public_id_from_url(url):
    """
    Try to derive the Cloudinary public_id from a Cloudinary delivery URL.
    Example delivery URL patterns:
      https://res.cloudinary.com/<cloud>/raw/upload/v123/media/materials/name.pdf
      /.../upload/v1/media/materials/name.pdf
    This strips the /upload/ prefix, removes the version (v123) if present,
    and removes the file extension.
    Returns a public_id string (may include folder path), or None if not parsable.
    """
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path  # e.g. /dae0htmcz/raw/upload/v1/media/materials/NAME.pdf
    if '/upload/' not in path:
        return None
    after = path.split('/upload/', 1)[1]
    parts = after.split('/')
    # remove version segment if it looks like v123
    if parts and parts[0].startswith('v') and parts[0][1:].isdigit():
        parts = parts[1:]
    if not parts:
        return None
    public_id_with_ext = '/'.join(parts)
    public_id = os.path.splitext(public_id_with_ext)[0]
    return public_id

def get_cloudinary_signed_or_public_url(material):
    """
    Given a Material instance, try to return a safe download URL:
    - If the file is a FieldFile uploaded through django-cloudinary-storage, material.file.name
      often equals public_id — prefer that.
    - Otherwise try to derive public_id from material.file_url.
    - Query Cloudinary for resource metadata. If resource is 'authenticated' or requires signing,
      generate a signed URL (type='authenticated', sign_url=True). Otherwise return public secure_url.
    - Fallback: return material.file_url (may fail if not accessible).
    """
    # Prefer the stored file name if present (django-cloudinary-storage typically stores public_id in .name)
    public_id = None
    try:
        # material.file may be FieldFile or a plain string
        if hasattr(material, "file") and getattr(material.file, "name", None):
            public_id = material.file.name
        # If not, try extracting from file_url
        if not public_id:
            public_id = extract_public_id_from_url(material.file_url)
        if not public_id:
            # nothing to derive — fall back to stored url (may be private)
            return material.file_url

        # Query Cloudinary for metadata (resource_type raw for PDF/docs)
        try:
            info = cloudinary.api.resource(public_id, resource_type='raw')
        except cloudinary.api.NotFound:
            # resource truly not found in Cloudinary -> fallback to stored URL
            return material.file_url
        except cloudinary.api.Forbidden:
            # Forbidden - likely needs signing as 'authenticated'
            # We'll attempt to build a signed URL below
            info = {"type": "authenticated"}
        except Exception:
            # Some other error querying API: fallback to stored URL
            return material.file_url

        # Decide whether the resource requires signing.
        # Common indicators: info['type']=='authenticated' OR info.get('access_control') presence.
        resource_type = info.get('resource_type', 'raw')
        is_authenticated = (info.get('type') == 'authenticated') or bool(info.get('access_control'))

        if is_authenticated:
            # Create a signed, time-limited URL for authenticated/raw resource.
            # Note: type='authenticated' is used for authenticated delivery; sign_url=True appends signature.
            url, _options = cloudinary_url(public_id,
                                           resource_type='raw',
                                           type='authenticated',
                                           sign_url=True)
            return url
        else:
            # Resource exists and is public; we can return a normal delivery URL via cloudinary_url
            url, _ = cloudinary_url(public_id, resource_type='raw', sign_url=False)
            return url

    except Exception:
        # Last resort: return whatever file_url is stored
        return material.file_url
