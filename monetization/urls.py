from django.urls import path, include
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
    path('activation/my_status/', UserActivationViewSet.as_view({'get': 'my_status'}), name='user-activation-my-status'),
    path('activation/verify_code/', UserActivationViewSet.as_view({'post': 'verify_code'}), name='user-activation-verify-code'),
    path('activation/monetization_info/', UserActivationViewSet.as_view({'get': 'monetization_info'}), name='monetization-info'),
]
