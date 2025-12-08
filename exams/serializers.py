# exams/serializers.py
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import (
    Course, Question, TestSession, GroupTest, Material,
    SpecialCourse, SpecialQuestion, SpecialChoice, SpecialEnrollment, SpecialAnswer, UserProfile
)

User = get_user_model()


class MaterialSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)  # File input for upload only
    file_url = serializers.SerializerMethodField()  # File URL for download
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Material
        fields = ['id', 'name', 'tags', 'file', 'file_url', 'course', 'course_name', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_url', 'course_name']

    def get_file_url(self, obj):
        """Return the stored Cloudinary URL"""
        return obj.file if obj.file else None


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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('registration_number', 'department', 'phone_number', 'role')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    is_staff = serializers.BooleanField(source='is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='is_superuser', read_only=True)
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser', 'profile']


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


# file upload helpers - keep as before
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


# Special course serializers
class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialChoice
        fields = ('id', 'text')


class SpecialQuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = SpecialQuestion
        fields = ('id', 'text', 'choices', 'mark')


class SpecialCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialCourse
        fields = ('id', 'title', 'description', 'start_time', 'end_time', 'duration_minutes')


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialEnrollment
        fields = ('id', 'user', 'course', 'enrolled_at', 'started', 'submitted', 'score')


class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choice = serializers.IntegerField(allow_null=True)


class SubmitExamSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)
