# Empty migration placeholder to match database state
# This migration is intentionally empty because the database already contains
# the EmailMessage table and the Material field alterations (applied outside
# of this codebase). Creating this empty migration ensures Django's migration
# graph matches the database without making schema changes.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0013_alter_material_tags'),
    ]

    operations = [
        # No operations: placeholder to sync migration history with DB
    ]
