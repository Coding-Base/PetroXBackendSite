from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView
)
from exams.views.auth import RegisterUserAPIView, GoogleAuthView
from exams.views import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('admin/trigger-send/', views.trigger_render_job, name='trigger_render_job'),
    path('users/', RegisterUserAPIView.as_view(), name='register-user-root'),
    path('api/auth/google/', GoogleAuthView.as_view(), name='google-auth'),
    path('api/', include('exams.urls')),
    path('api/', include('updates.urls')),  # Add this line to include updates URLs
]

