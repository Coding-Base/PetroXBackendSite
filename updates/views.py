# updates/views.py
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Update, Comment, Like, UpdateReadState
from .serializers import UpdateSerializer, CommentSerializer, LikeSerializer

logger = logging.getLogger(__name__)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow safe methods for everyone; non-safe methods only for staff users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class UpdateViewSet(viewsets.ModelViewSet):
    """
    CRUD for Update (announcements/blogs). Non-staff users can read only.
    Provides extra actions and temporarily force-cors for debugging.
    """
    queryset = Update.objects.filter(published=True).order_by('-created_at')
    serializer_class = UpdateSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    # ---------- Helper: the origin to allow (temporary) ----------
    # Use the exact frontend origin you serve from
    FRONTEND_ORIGIN = "https://petrox-test-frontend.onrender.com"

    # ---------- Overriding OPTIONS to ensure preflight response is correct ----------
    def options(self, request, *args, **kwargs):
        """
        Ensure OPTIONS replies include the Access-Control headers the browser expects.
        This is a temporary debugging aid; normally django-cors-headers handles this.
        """
        response = super().options(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = self.FRONTEND_ORIGIN
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'authorization, content-type, x-upload-timeout'
        # If you use cookies, set to 'true' and set CORS_ALLOW_CREDENTIALS accordingly.
        response['Access-Control-Allow-Credentials'] = 'false'
        response['Access-Control-Max-Age'] = '86400'
        return response

    # ---------- Ensure list() sets CORS headers and logs arrival ----------
    def list(self, request, *args, **kwargs):
        """
        Override list to log and add response headers to prevent shared caches
        and ensure the browser accepts the response.
        """
        logger.debug("UpdateViewSet.list called by %s (origin: %s)", request.META.get('REMOTE_ADDR'), request.META.get('HTTP_ORIGIN'))
        response = super().list(request, *args, **kwargs)

        # Disable caching for the updates feed
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        # Force the Access-Control headers (temporary)
        response['Access-Control-Allow-Origin'] = self.FRONTEND_ORIGIN
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'authorization, content-type, x-upload-timeout'
        response['Access-Control-Allow-Credentials'] = 'false'

        return response

    # ---------- A safety net: ensure final response includes CORS if missing ----------
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if 'Access-Control-Allow-Origin' not in response:
            response['Access-Control-Allow-Origin'] = self.FRONTEND_ORIGIN
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'authorization, content-type, x-upload-timeout'
            response['Access-Control-Allow-Credentials'] = 'false'
        return response

    # ---------- Existing actions (like/unlike/etc) kept intact ----------
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, slug=None):
        update = self.get_object()
        try:
            like, created = Like.objects.get_or_create(user=request.user, update=update)
            if not created:
                return Response({'detail': 'already liked'}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'detail': 'already liked'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'liked', 'like_id': like.id}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, slug=None):
        update = self.get_object()
        Like.objects.filter(user=request.user, update=update).delete()
        return Response({'status': 'unliked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def like_status(self, request, slug=None):
        update = self.get_object()
        liked = Like.objects.filter(user=request.user, update=update).exists()
        return Response({'liked': liked}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unread_count(self, request):
        unread = Update.objects.filter(published=True).exclude(
            id__in=UpdateReadState.objects.filter(user=request.user, viewed=True).values_list('update_id', flat=True)
        ).count()
        return Response({'unread_count': unread}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_all_read(self, request):
        user = request.user
        now = timezone.now()
        updates = Update.objects.filter(published=True)
        for u in updates:
            state, _ = UpdateReadState.objects.get_or_create(user=user, update=u)
            state.viewed = True
            state.viewed_at = now
            state.save()
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    """
    Comments and replies for updates. Root comments return with parent=None.
    Supports ?update=<id> to filter comments for a specific update.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        update_id = self.request.query_params.get('update')
        qs = Comment.objects.select_related('user').all()
        if update_id:
            return qs.filter(update_id=update_id, parent__isnull=True).prefetch_related('replies')
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
