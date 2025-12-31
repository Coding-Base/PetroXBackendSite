"""
lecturer_dashboard/views.py
Views for lecturer dashboard
"""
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LecturerAccount
from .serializers import LecturerAccountSerializer, LecturerRegistrationSerializer
import logging

logger = logging.getLogger(__name__)


class LecturerRegisterView(APIView):
    """View to register a new lecturer"""
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
            logger.error(f"Lecturer registration error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Registration failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LecturerProfileView(APIView):
    """View to get/update lecturer profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            lecturer_account = LecturerAccount.objects.get(user=request.user)
            serializer = LecturerAccountSerializer(lecturer_account)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except LecturerAccount.DoesNotExist:
            return Response({
                'error': 'Lecturer account not found',
                'detail': 'This user is not registered as a lecturer'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching lecturer profile: {str(e)}", exc_info=True)
            return Response({
                'error': 'Error fetching profile',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            lecturer_account = LecturerAccount.objects.get(user=request.user)
            serializer = LecturerAccountSerializer(lecturer_account, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except LecturerAccount.DoesNotExist:
            return Response({
                'error': 'Lecturer account not found'
            }, status=status.HTTP_404_NOT_FOUND)
