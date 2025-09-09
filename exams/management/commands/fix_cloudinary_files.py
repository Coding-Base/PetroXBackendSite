# exams/management/commands/fix_cloudinary_files.py
import os
import tempfile
import requests
from django.core.management.base import BaseCommand
from django.core.files import File
from exams.models import Material

class Command(BaseCommand):
    help = "Re-upload existing Material.file_url to Cloudinary via Django storage"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Limit records (0=all)")
        parser.add_argument("--start-id", type=int, default=0, help="Start id")

    def handle(self, *args, **options):
        limit = options["limit"]
        start_id = options["start_id"]

        qs = Material.objects.filter(id__gte=start_id).order_by("id")
        if limit:
            qs = qs[:limit]

        for m in qs:
            url = m.file_url
            if not url:
                self.stdout.write(f"Skipping id={m.id}: no file_url")
                continue
            self.stdout.write(f"Processing id={m.id}: {url}")
            try:
                r = requests.get(url, stream=True, timeout=60)
                r.raise_for_status()
                suffix = os.path.splitext(url)[1] or ".pdf"
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                for chunk in r.iter_content(1024 * 1024):
                    tmp.write(chunk)
                tmp.flush(); tmp.close()
                with open(tmp.name, "rb") as fh:
                    name = f"materials/{m.id}{suffix}"
                    m.file.save(name, File(fh), save=True)
                os.remove(tmp.name)
                self.stdout.write(self.style.SUCCESS(f"Updated id={m.id}"))
            except Exception as e:
                self.stderr.write(f"Failed id={m.id}: {e}")
