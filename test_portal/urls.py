# test_portal/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from exams.views.auth  import  RegisterUserAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Expose user registration at the root /users/ URL
    path('users/', RegisterUserAPIView.as_view(), name='register-user-root'),

    # All other exam-related API routes under /api/
    path('api/', include('exams.urls')),
]