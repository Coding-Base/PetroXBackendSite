from django.urls import path, include
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter
from .views import (
    MonetizationSettingsViewSet,
    ActivationCodeViewSet,
    UserActivationViewSet
)

router = DefaultRouter()
router.register(r'settings', MonetizationSettingsViewSet, basename='monetization-settings')
router.register(r'codes', ActivationCodeViewSet, basename='activation-codes')
router.register(r'activation', UserActivationViewSet, basename='user-activation')

urlpatterns = [
    path('', include(router.urls)),
    # Explicitly expose important actions in case router registration is missed
    # Temporary health-check endpoint to verify monetization urls are included in deployment
    path('activation/ping/', lambda request: HttpResponse('monetization ok'), name='monetization-ping'),
    path('activation/my_status/', UserActivationViewSet.as_view({'get': 'my_status'}), name='user-activation-my-status'),
    path('activation/verify_code/', UserActivationViewSet.as_view({'post': 'verify_code'}), name='user-activation-verify-code'),
    path('activation/monetization_info/', UserActivationViewSet.as_view({'get': 'monetization_info'}), name='monetization-info'),
]
