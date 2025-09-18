from rest_framework import serializers
from .models import Update, Comment, Like, UpdateReadState
from django.contrib.auth import get_user_model


User = get_user_model()


class RecursiveSerializer(serializers.Serializer):
def to_representation(self, value):
serializer = self.parent.parent.__class__(value, context=self.context)
return serializer.data


class CommentSerializer(serializers.ModelSerializer):
user_name = serializers.SerializerMethodField()
replies = serializers.ListSerializer(child=RecursiveSerializer(), source='replies', read_only=True)


class Meta:
model = Comment
fields = ('id','update','user','user_name','parent','body','created_at','replies')
read_only_fields = ('user','user_name','created_at')


def get_user_name(self, obj):
return obj.user.get_full_name() or obj.user.username


def create(self, validated_data):
request = self.context.get('request')
validated_data['user'] = request.user
return super().create(validated_data)


class UpdateSerializer(serializers.ModelSerializer):
like_count = serializers.IntegerField(source='likes.count', read_only=True)
comment_count = serializers.IntegerField(source='comments.count', read_only=True)


class Meta:
model = Update
fields = ('id','title','slug','body','author','created_at','updated_at','published','featured_image','like_count','comment_count')
read_only_fields = ('author','created_at','updated_at','like_count','comment_count')


def create(self, validated_data):
request = self.context.get('request')
validated_data['author'] = request.user
return super().create(validated_data)


class LikeSerializer(serializers.ModelSerializer):
class Meta:
model = Like
fields = ('id','user','update','created_at')
read_only_fields = ('user','created_at')


def create(self, validated_data):
validated_data['user'] = self.context['request'].user
return super().create(validated_data)