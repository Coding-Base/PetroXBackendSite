"""
Management command to check and fix materials in the database.
"""
from django.core.management.base import BaseCommand
from exams.models import Material


class Command(BaseCommand):
    help = 'Debug and check materials in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix materials with missing URLs (in development only)',
        )

    def handle(self, *args, **options):
        materials = Material.objects.all()
        total = materials.count()
        self.stdout.write(f"Total materials in database: {total}")
        self.stdout.write("-" * 80)

        if total == 0:
            self.stdout.write(self.style.WARNING("No materials found in database!"))
            return

        # Check materials
        with_url = 0
        without_url = 0
        for m in materials:
            has_url = bool(m.file)
            if has_url:
                with_url += 1
                self.stdout.write(f"✓ ID {m.id}: {m.name}")
                self.stdout.write(f"  URL: {m.file[:60]}...")
            else:
                without_url += 1
                self.stdout.write(self.style.ERROR(f"✗ ID {m.id}: {m.name} (NO URL)"))

        self.stdout.write("-" * 80)
        self.stdout.write(f"Summary: {with_url} with URL, {without_url} without URL")

        if without_url > 0:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  {without_url} materials are missing file URLs!"
            ))
            self.stdout.write(
                "These materials will not appear in search results."
            )
            self.stdout.write(
                "You need to re-upload these materials to add their URLs."
            )
