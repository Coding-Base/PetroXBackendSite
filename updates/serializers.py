# updates/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Update, Comment, Like, UpdateReadState

User = get_user_model()


class UserLiteSerializer(serializers.ModelSerializer):
    """Small user representation for comments/author fields."""
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class CommentSerializer(serializers.ModelSerializer):
    """
    Comment serializer:
     - user is read-only (populated from request in view or here)
     - replies is computed via get_replies (avoids source='replies' redundancy)
    """
    user = UserLiteSerializer(read_only=True)
    user_name = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "update", "user", "user_name", "parent", "body", "created_at", "replies")
        read_only_fields = ("user", "user_name", "created_at", "replies")

    def get_user_name(self, obj):
        if getattr(obj, "user", None):
            return obj.user.get_full_name() or obj.user.username
        return None

    def get_replies(self, obj):
        # return direct children replies serialized
        qs = obj.replies.all().order_by("created_at")  # assumes related_name="replies"
        return CommentSerializer(qs, many=True, context=self.context).data

    def create(self, validated_data):
        # prefer view to call serializer.save(user=request.user) but be defensive here
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


class UpdateSerializer(serializers.ModelSerializer):
    """
    Update serializer. Keeps the same fields you had originally.
    like_count and comment_count are computed to avoid reliance on model fields.
    """
    like_count = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    author = UserLiteSerializer(read_only=True)

    class Meta:
        model = Update
        fields = (
            "id", "title", "slug", "body", "author",
            "created_at", "updated_at", "published", "featured_image",
            "like_count", "comment_count",
        )
        read_only_fields = ("author", "created_at", "updated_at", "like_count", "comment_count")

    def create(self, validated_data):
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["author"] = user
        return super().create(validated_data)

    def get_like_count(self, obj):
        # prefer prefetched/annotated attribute if present
        if hasattr(obj, "likes_count"):
            return obj.likes_count
        # if relation exists
        if hasattr(obj, "likes"):
            return obj.likes.count()
        # fallback
        return Like.objects.filter(update=obj).count()

    def get_comment_count(self, obj):
        if hasattr(obj, "comments_count"):
            return obj.comments_count
        if hasattr(obj, "comments"):
            return obj.comments.count()
        return Comment.objects.filter(update=obj).count()


class LikeSerializer(serializers.ModelSerializer):
    user = UserLiteSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ("id", "user", "update", "created_at")
        read_only_fields = ("id", "user", "created_at")

    def create(self, validated_data):
        request = self.context.get("request", None)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)
