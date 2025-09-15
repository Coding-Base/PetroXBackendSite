from django.core.management.base import BaseCommand
from exams.models import Material
from django.conf import settings
import os

class Command(BaseCommand):
    help = "Convert Material.file relative paths to public Cloudinary URLs (idempotent)."

    def handle(self, *args, **options):
        # cloud name from settings or env
        cloud_name = None
        cfg = getattr(settings, "CLOUDINARY_STORAGE", None)
        if cfg and isinstance(cfg, dict):
            cloud_name = cfg.get("CLOUD_NAME")
        if not cloud_name:
            cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME") or os.environ.get("CLOUD_NAME")

        if not cloud_name:
            self.stderr.write("CLOUDINARY_CLOUD_NAME not set; aborting.")
            return

        updated = 0
        for mat in Material.objects.all():
            f = getattr(mat, "file", None)
            if not f:
                continue
            # Skip absolute URLs
            if isinstance(f, str) and (f.startswith("http://") or f.startswith("https://") or f.startswith("//")):
                continue

            # If it's FieldFile-like string with leading media/ remove
            fname = str(f).lstrip("/")
            fname = fname.replace("media/", "").replace("media/media/", "")
            new_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{fname}"
            mat.file = new_url
            mat.save(update_fields=["file"])
            updated += 1

        self.stdout.write(f"Updated {updated} materials to Cloudinary public URLs.")
