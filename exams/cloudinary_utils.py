import cloudinary
import cloudinary.utils
import time

def get_cloudinary_signed_or_public_url(material, expires_in=3600):
    """
    Generate a signed Cloudinary URL if file is private.
    Returns direct public URL if file is public.
    """
    if not material.file:
        return None

    # Cloudinary stores full path in file.name (e.g., media/materials/file.pdf)
    # Remove the storage prefix to get the public_id
    public_id = material.file.name.replace("media/", "").replace("materials/", "").split(".")[0]

    try:
        # Signed URL valid for `expires_in` seconds
        signed_url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="raw",          # needed for pdf/doc
            type="authenticated",         # ensure signed delivery
            sign_url=True,
            expires_at=int(time.time()) + expires_in
        )
        return signed_url
    except Exception:
        # fallback: plain file url (works if file is public)
        return material.file.url
