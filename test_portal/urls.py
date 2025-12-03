# test_portal/urls.py
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

# Import auth views and the trigger_render_job directly from the modules that contain them
from exams.views.auth import RegisterUserAPIView, GoogleAuthView
from exams.views.views import trigger_render_job

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Admin endpoint to trigger Render one-off job (admin-protected view)
    path('admin/trigger-send/', trigger_render_job, name='trigger_render_job'),

    # Auth endpoints
    path('users/', RegisterUserAPIView.as_view(), name='register-user-root'),
    path('api/auth/google/', GoogleAuthView.as_view(), name='google-auth'),

    # app includes
    path('api/', include('exams.urls')),
    path('api/', include('updates.urls')),
    path('api/monetization/', include('monetization.urls')),
]
