"""
lecturer_dashboard/apps.py
App configuration for lecturer dashboard
"""
from django.apps import AppConfig


class LecturerDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lecturer_dashboard'
    verbose_name = 'Lecturer Dashboard'
