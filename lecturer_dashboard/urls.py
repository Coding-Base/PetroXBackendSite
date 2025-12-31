"""
lecturer_dashboard/urls.py
URL routes for lecturer dashboard
"""
from django.urls import path
from .views import LecturerRegisterView, LecturerProfileView

app_name = 'lecturer_dashboard'

urlpatterns = [
    path('register/', LecturerRegisterView.as_view(), name='lecturer-register'),
    path('profile/', LecturerProfileView.as_view(), name='lecturer-profile'),
]
