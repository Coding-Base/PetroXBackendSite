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
]
