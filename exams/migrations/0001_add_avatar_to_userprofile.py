# Generated migration to add avatar field to UserProfile
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = False

    dependencies = [
        # Update these to match your project state if necessary
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.URLField(max_length=1000, null=True, blank=True),
        ),
    ]
