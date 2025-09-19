# updates/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Update, Comment, Like

User = get_user_model()


class UserLiteSerializer(serializers.ModelSerializer):
    """Small user representation for comments/author fields."""
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment objects.
    - `user` is read-only and populated from request in the view (or perform_create).
    - `replies` is computed via a method to avoid circular serializer references and
      to permit unlimited nested replies.
    """
    user = UserLiteSerializer(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "update", "body", "parent", "user", "created_at", "replies")
        read_only_fields = ("id", "user", "created_at", "replies")

    def get_replies(self, obj):
        """
        Return serialized list of replies (direct children) for this comment.
        Assumes Comment model has related_name="replies" on parent FK.
        """
        # Ensure we prefetch in queryset on the view for performance if needed
        qs = obj.replies.all().order_by("created_at")
        return CommentSerializer(qs, many=True, context=self.context).data

    def validate_parent(self, parent):
        """
        Optional: ensure the parent (if provided) belongs to the same update.
        """
        if parent and parent.update_id != self.initial_data.get("update"):
            raise serializers.ValidationError("Parent comment must belong to the same update.")
        return parent

    def create(self, validated_data):
        """
        If the view doesn't call serializer.save(user=request.user),
        we ensure the user is assigned here from the context (if available).
        This keeps clients from specifying the user in the payload.
        """
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


class LikeSerializer(serializers.ModelSerializer):
    user = UserLiteSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "user", "update", "created_at")
        read_only_fields = ("id", "user", "created_at")


class UpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Update (announcement/blog).
    Adds convenience fields for counts (like_count, comment_count).
    """
    author = UserLiteSerializer(source="author", read_only=True)
    like_count = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Update
        # include fields your frontend needs; add/remove as needed
        fields = (
            "id",
            "title",
            "slug",
            "body",
            "excerpt",
            "featured_image",
            "published",
            "created_at",
            "updated_at",
            "author",
            "like_count",
            "comment_count",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at", "author", "like_count", "comment_count")

    def get_like_count(self, obj):
        # If you prefetch, this is cheap; otherwise this triggers a query
        return getattr(obj, "likes_count", obj.likes.count() if hasattr(obj, "likes") else Like.objects.filter(update=obj).count())

    def get_comment_count(self, obj):
        return getattr(obj, "comments_count", obj.comments.count() if hasattr(obj, "comments") else Comment.objects.filter(update=obj).count())
