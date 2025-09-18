# updates/views.py
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import Update, Comment, Like, UpdateReadState
from .serializers import UpdateSerializer, CommentSerializer, LikeSerializer


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
    Provides extra actions:
      - POST /api/updates/{slug}/like/
      - POST /api/updates/{slug}/unlike/
      - GET  /api/updates/{slug}/like_status/
      - GET  /api/updates/unread_count/
      - POST /api/updates/mark_all_read/
    """
    queryset = Update.objects.filter(published=True).order_by('-created_at')
    serializer_class = UpdateSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, slug=None):
        """
        Like an update. Idempotent in effect: returns 400 if already liked.
        """
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
        """
        Unlike an update. Always returns success even if there was no previous like.
        """
        update = self.get_object()
        Like.objects.filter(user=request.user, update=update).delete()
        return Response({'status': 'unliked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def like_status(self, request, slug=None):
        """
        Return whether the current user has liked this update.
        GET /api/updates/{slug}/like_status/ -> { "liked": true|false }
        """
        update = self.get_object()
        liked = Like.objects.filter(user=request.user, update=update).exists()
        return Response({'liked': liked}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unread_count(self, request):
        """
        Return count of unread updates for the current user.
        This implementation uses UpdateReadState entries (one per user+update).
        Consider switching to last_viewed_at on user profile for better scale.
        """
        unread = Update.objects.filter(published=True).exclude(
            id__in=UpdateReadState.objects.filter(user=request.user, viewed=True).values_list('update_id', flat=True)
        ).count()
        return Response({'unread_count': unread}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_all_read(self, request):
        """
        Mark all current published updates as read for the current user.
        """
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
            # return only root comments (parent is null) and prefetch replies
            return qs.filter(update_id=update_id, parent__isnull=True).prefetch_related('replies')
        return qs

    def perform_create(self, serializer):
        # set the comment author from the authenticated user
        serializer.save(user=self.request.user)
