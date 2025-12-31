# exams/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Course, Question, TestSession, GroupTest, Material
import uuid
from django.conf import settings


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


from rest_framework import serializers
from .models import SpecialCourse, SpecialQuestion, SpecialChoice, SpecialEnrollment, SpecialAnswer, UserProfile
from django.conf import settings

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialChoice
        fields = ('id','text')

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SpecialQuestion
        fields = ('id','text','choices','mark','image','image_url')
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class SpecialCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialCourse
        fields = ('id','title','description','start_time','end_time','duration_minutes')

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialEnrollment
        fields = ('id','user','course','enrolled_at','started','submitted','score')

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
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
    
    def create(self, validated_data):
        from django.contrib.auth.models import User
        from django.db import IntegrityError, ProgrammingError
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            username = validated_data['username']
            email = validated_data['email']
            password = validated_data['password']
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Note: LecturerAccount is created in lecturer_dashboard app
            # This serializer now only creates the User object
            # The lecturer profile is created via /api/lecturer/register/
            
            return user
        except IntegrityError as e:
            logger.error(f"IntegrityError during lecturer registration: {str(e)}")
            if 'username' in str(e).lower():
                raise serializers.ValidationError({"username": "Username already exists."})
            elif 'email' in str(e).lower():
                raise serializers.ValidationError({"email": "Email already registered."})
            else:
                raise serializers.ValidationError({"detail": "Registration failed. Please try again."})
        except Exception as e:
            logger.error(f"Error during lecturer registration: {str(e)}", exc_info=True)
            raise serializers.ValidationError({"detail": str(e)})

