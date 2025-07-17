# test_portal/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from exams.views.auth import RegisterUserAPIView,GoogleAuthView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    path('users/', RegisterUserAPIView.as_view(), name='register-user-root'),
    path('api/auth/google/', GoogleAuthView.as_view(), name='google-auth'),  # Add this line
    path('api/', include('exams.urls')),
]