# Generated by Django 5.1.6 on 2025-05-31 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0002_course_description_alter_course_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsession',
            name='question_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
