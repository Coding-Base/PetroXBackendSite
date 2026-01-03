import logging
import requests
import re
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import GoogleAuthError

# --- NEW IMPORTS FOR JWT ---
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
# ---------------------------

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError
from django.db.utils import DataError
from ..serializers import UserSerializer
from ..models import UserProfile
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

# =========================================================
#  1. CUSTOM JWT SERIALIZER & VIEW (Add this section)
# =========================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Serializer to add 'role' and 'username' to the 
    login response payload.
    """
    def validate(self, attrs):
        # 1. Standard validation (checks username/password)
        data = super().validate(attrs)

        # 2. Determine User Role
        # Default role is student
        role = 'student'
        
        # We use a local import here to prevent potential circular import issues
        # between apps (exams <-> lecturer_dashboard)
        try:
            from lecturer_dashboard.models import LecturerAccount
            if LecturerAccount.objects.filter(user=self.user).exists():
                role = 'lecturer'
        except ImportError:
            logger.warning("Could not import LecturerAccount model")

        # 3. Add custom data to response
        data['role'] = role
        data['username'] = self.user.username
        data['id'] = self.user.id
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom View to use our serializer
    """
    serializer_class = CustomTokenObtainPairSerializer


# =========================================================
#  EXISTING VIEWS (Kept as they were)
# =========================================================

class RegisterUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        registration_number = request.data.get('registration_number', '')
        department = request.data.get('department', '')

        # Add email validation
        if not username or not password:
            raise ValidationError({"detail": "Username and password are required."})
        
        if not email:
            raise ValidationError({"detail": "Email is required."})

        try:
            user = User.objects.create_user(
                username=username,
                email=email,  # Make sure email is included
                password=password
            )
            
            # Create UserProfile with registration_number and department
            if registration_number or department:
                UserProfile.objects.create(
                    user=user,
                    registration_number=registration_number if registration_number else None,
                    department=department
                )
            
        except IntegrityError as e:
            if 'username' in str(e).lower():
                return Response(
                    {"detail": "Username already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'email' in str(e).lower():
                return Response(
                    {"detail": "Email already registered."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'registration_number' in str(e).lower():
                return Response(
                    {"detail": "Registration number already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"detail": "Registration failed. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:  # Catch other potential errors
            logger.error(f"Registration error: {str(e)}")
            return Response(
                {"detail": "Could not create user. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentUserRoleView(APIView):
    """API view to get current authenticated user's role"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Check if lecturer first
            from lecturer_dashboard.models import LecturerAccount
            if LecturerAccount.objects.filter(user=request.user).exists():
                 return Response({
                    'username': request.user.username,
                    'email': request.user.email,
                    'role': 'lecturer',
                    'id': request.user.id
                }, status=status.HTTP_200_OK)

            # Then check student profile
            profile = UserProfile.objects.get(user=request.user)
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'role': 'student',
                'id': request.user.id
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            # Default fallback
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'role': 'student',
                'id': request.user.id
            }, status=status.HTTP_200_OK)


from rest_framework.renderers import JSONRenderer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class GoogleAuthView(APIView):
    permission_classes = []
    
    def post(self, request):
        # Return a simple test response
        return Response({
            'test': 'success',
            'message': 'Google auth endpoint is working'
        }, status=status.HTTP_200_OK)
