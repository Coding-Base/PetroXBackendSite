from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from django.db import IntegrityError
from ..serializers import UserSerializer, LecturerRegistrationSerializer, UserProfileSerializer
from rest_framework.exceptions import ValidationError
from ..models import Course, Question, TestSession, GroupTest, UserProfile
from ..serializers import CourseSerializer, GroupTestSerializer
from rest_framework import generics

class CourseListAPIView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

class RegisterUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not password:
            raise ValidationError({"detail": "Username and password are required."})

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            # Create default student profile
            UserProfile.objects.create(user=user)
        except IntegrityError:
            return Response(
                {"detail": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LecturerRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            serializer = LecturerRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'message': 'Lecturer account created successfully'
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Lecturer registration error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Registration failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)