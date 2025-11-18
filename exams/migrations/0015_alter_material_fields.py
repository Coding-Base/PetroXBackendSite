# Migration to explicitly increase Material.name and Material.tags column lengths
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0013_alter_material_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='material',
            name='tags',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
