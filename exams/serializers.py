from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Course, Question, TestSession, GroupTest, Material
# removed google.cloud import
import uuid
from django.conf import settings

class MaterialSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = ['id', 'name', 'tags', 'file', 'file_url', 'course', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_url']
        extra_kwargs = {
            'file': {'write_only': True},
        }

    def get_file_url(self, obj):
        return obj.file_url

    def create(self, validated_data):
        # The user is now handled in the view, so we don't need to pop it here
        uploaded_file = validated_data.pop('file', None)

        # Create material instance without file first
        material = Material.objects.create(**validated_data)

        if uploaded_file:
            # Assign file and save through storage (now Cloudinary via DEFAULT_FILE_STORAGE)
            material.file.save(
                uploaded_file.name,
                uploaded_file,
                save=True
            )

        return material

class GroupTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupTest
        fields = [
            'id',
            'name',
            'course',
            'question_count',
            'duration_minutes',
            'created_by',
            'invitees',
            'scheduled_start',
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class TestSessionSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    class Meta:
        model = TestSession
        fields = ['id', 'user', 'course', 'questions', 'start_time', 'end_time', 'score', 'duration', 'question_count']

# New serializer for preview endpoint
class PreviewPassQuestionsSerializer(serializers.Serializer):
    file = serializers.FileField()
    question_type = serializers.ChoiceField(choices=[('multichoice', 'Multiple Choice')])

class BulkQuestionSerializer(serializers.Serializer):
    file = serializers.FileField()
    course_id = serializers.IntegerField()
    question_type = serializers.ChoiceField(choices=[('multichoice', 'Multiple Choice')])

    def validate_course_id(self, value):
        if not Course.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid course ID")
        return value

class QuestionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'status', 'question_text']
        read_only_fields = ['id', 'question_text']
