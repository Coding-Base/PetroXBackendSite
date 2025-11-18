# Generated migration to increase Material.tags field length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0012_question_year'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='tags',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
