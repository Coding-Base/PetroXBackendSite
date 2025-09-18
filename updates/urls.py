from rest_framework.routers import DefaultRouter
from .views import UpdateViewSet, CommentViewSet


router = DefaultRouter()
router.register('updates', UpdateViewSet, basename='updates')
router.register('comments', CommentViewSet, basename='comments')


urlpatterns = router.urls