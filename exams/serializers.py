# exams/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Course, Question, TestSession, GroupTest, Material, 
    SpecialCourse, SpecialQuestion, SpecialChoice, 
    SpecialEnrollment, SpecialAnswer, UserProfile
)
import uuid
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# ==========================================
#  1. GENERAL FEATURES SERIALIZERS
# ==========================================

class MaterialSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)
    file_url = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Material
        fields = ['id', 'name', 'tags', 'file', 'file_url', 'course', 'course_name', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at', 'file_url', 'course_name']

    def get_file_url(self, obj):
        return obj.file if obj.file else None


class GroupTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupTest
        fields = [
            'id', 'name', 'course', 'question_count', 'duration_minutes',
            'created_by', 'invitees', 'scheduled_start'
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


# ==========================================
#  2. SPECIAL EXAMS: STUDENT VIEW (SECURE)
# ==========================================

class ChoiceSerializer(serializers.ModelSerializer):
    """
    For Students: Hides the 'is_correct' field so they cannot cheat via network inspection.
    """
    class Meta:
        model = SpecialChoice
        fields = ('id', 'text') 

class SpecialQuestionSerializer(serializers.ModelSerializer):
    """
    For Students: Uses the secure ChoiceSerializer.
    """
    choices = ChoiceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SpecialQuestion
        fields = ('id', 'text', 'choices', 'mark', 'image', 'image_url')
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


# ==========================================
#  3. SPECIAL EXAMS: LECTURER VIEW (FULL ACCESS)
# ==========================================

class LecturerChoiceSerializer(serializers.ModelSerializer):
    """
    For Lecturers: Includes 'is_correct' so they can verify answers in the dashboard.
    """
    class Meta:
        model = SpecialChoice
        fields = ('id', 'text', 'is_correct')

class LecturerQuestionSerializer(serializers.ModelSerializer):
    """
    For Lecturers: Uses the full LecturerChoiceSerializer.
    """
    choices = LecturerChoiceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SpecialQuestion
        fields = ('id', 'course', 'text', 'choices', 'mark', 'image', 'image_url')

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


# ==========================================
#  4. SPECIAL EXAMS: SHARED & UTILS
# ==========================================

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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('registration_number', 'department', 'role')


class LecturerRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=255)
    department = serializers.CharField(max_length=255)
    faculty = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
    
    def create(self, validated_data):
        from django.db import IntegrityError
        
        try:
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            # LecturerAccount creation is handled in the View, not here
            return user
        except IntegrityError as e:
            logger.error(f"IntegrityError: {str(e)}")
            if 'username' in str(e).lower():
                raise serializers.ValidationError({"username": "Username already exists."})
            elif 'email' in str(e).lower():
                raise serializers.ValidationError({"email": "Email already registered."})
            else:
                raise serializers.ValidationError({"detail": "Registration failed."})
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise serializers.ValidationError({"detail": str(e)})

