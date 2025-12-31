"""
lecturer_dashboard/serializers.py
Serializers for lecturer dashboard
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import LecturerAccount


class LecturerAccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = LecturerAccount
        fields = ('id', 'username', 'email', 'name', 'department', 'faculty', 'phone', 'bio', 'is_verified', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class LecturerRegistrationSerializer(serializers.Serializer):
    """Serializer for lecturer registration"""
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
        """Create user and lecturer account"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Create user
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )

            # Create lecturer account
            lecturer_account = LecturerAccount.objects.create(
                user=user,
                name=validated_data['name'],
                department=validated_data['department'],
                faculty=validated_data['faculty'],
                phone=validated_data['phone']
            )

            return user
        except Exception as e:
            logger.error(f"Error during lecturer registration: {str(e)}", exc_info=True)
            raise serializers.ValidationError({"detail": str(e)})
