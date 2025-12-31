"""
lecturer_dashboard/models.py
Extended lecturer models separate from core exams app
"""
from django.db import models
from django.contrib.auth.models import User


class LecturerAccount(models.Model):
    """Lecturer account profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_account')
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    faculty = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    bio = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'lecturer_dashboard'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.department})"
