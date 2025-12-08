# exams/views/auth.py
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from ..serializers import UserSerializer, UserProfileSerializer
from ..models import UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class RegisterUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        registration_number = request.data.get('registration_number', '')
        department = request.data.get('department', '')
        phone_number = request.data.get('phone_number', '')
        full_name = request.data.get('full_name', '')  # optional
        role = request.data.get('role', 'student')  # 'student' or 'lecturer'

        # Basic validation
        if not username or not password:
            raise ValidationError({"detail": "Username and password are required."})

        if not email:
            raise ValidationError({"detail": "Email is required."})

        # Additional validation for lecturer
        if role == 'lecturer':
            if not department:
                raise ValidationError({"detail": "Department is required for lecturer accounts."})
            if not phone_number:
                raise ValidationError({"detail": "Phone number is required for lecturer accounts."})

        try:
            # create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # set extra flags for lecturer
            if role == 'lecturer':
                try:
                    user.is_staff = True  # give staff permission (so lecturers can access admin features)
                    user.save()
                except Exception:
                    # ignore failures to set flags but continue
                    logger.exception("Failed to set is_staff on lecturer user")

            # create profile
            profile = UserProfile.objects.create(
                user=user,
                registration_number=registration_number if registration_number else None,
                department=department,
                phone_number=phone_number if phone_number else None,
                role=role if role in ['student', 'lecturer'] else 'student'
            )

        except IntegrityError as e:
            logger.exception("IntegrityError creating user: %s", e)
            msg = str(e).lower()
            if 'username' in msg:
                return Response({"detail": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)
            if 'email' in msg:
                return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)
            if 'registration_number' in msg:
                return Response({"detail": "Registration number already exists."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Registration failed. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Registration error: %s", e)
            return Response({"detail": "Could not create user. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """
    Accepts: username, password
    Returns: { access, refresh, user: { ... } }
    This ensures frontend can detect lecturer via user.profile.role or user.is_staff
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"detail": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        # create tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Compose response with user serialization
        user_data = UserSerializer(user).data

        return Response({
            "access": access_token,
            "refresh": refresh_token,
            "user": user_data
        }, status=status.HTTP_200_OK)


# Simple test/debug endpoint already present in your file — leave unchanged or update as desired.
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
