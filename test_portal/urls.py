# test_portal/urls.py
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
    # TokenObtainPairView,  <-- REMOVED THIS, WE USE OUR CUSTOM ONE NOW
)

# Import our new custom view
from exams.views.auth import RegisterUserAPIView, GoogleAuthView, CurrentUserRoleView, CustomTokenObtainPairView
from exams.views.views import trigger_render_job

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # === CHANGED THIS LINE ===
    # Using CustomTokenObtainPairView instead of the default one
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # =========================

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Admin endpoint to trigger Render one-off job (admin-protected view)
    path('admin/trigger-send/', trigger_render_job, name='trigger_render_job'),

    # Auth endpoints
    path('users/', RegisterUserAPIView.as_view(), name='register-user-root'),
    path('api/auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('api/auth/me/', CurrentUserRoleView.as_view(), name='current-user-role'),

    # app includes
    path('api/', include('exams.urls')),
    path('api/', include('lecturer_dashboard.urls')),
    path('api/', include('updates.urls')),
    path('api/monetization/', include('monetization.urls')),
    # Also expose monetization endpoints at the non-API root for compatibility
    path('monetization/', include('monetization.urls')),
]
