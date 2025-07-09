from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.utils import timezone
import logging
from ..models import Material
from ..serializers import MaterialSerializer
from rest_framework.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

class MaterialUploadView(generics.CreateAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        server_time = timezone.now()
        logger.info(f"Upload request received at: {server_time}")
        
        if 'file' not in request.FILES:
            logger.warning("Upload attempt with no file")
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Log request details for debugging
            logger.info(f"Upload request by user: {request.user.id}")
            logger.info(f"File: {request.FILES['file'].name}")
            logger.info(f"Course ID: {request.data.get('course')}")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            material = serializer.save(uploaded_by=request.user)
            
            # Log successful upload
            logger.info(f"Material uploaded successfully: {material.id}")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ServiceUnavailable as e:
            logger.error(f"Storage service unavailable: {str(e)}")
            return Response({
                "error": "storage_unavailable",
                "message": "Storage service is currently unavailable. Please try again later."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except PermissionError as e:
            logger.error(f"GCS authentication error: {str(e)}")
            return Response({
                "error": "storage_authentication_failed",
                "message": "Storage authentication failed. Please contact support."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except RuntimeError as e:
            logger.error(f"GCS upload error: {str(e)}")
            return Response({
                "error": "upload_failed",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Unexpected upload error")
            return Response({
                "error": "internal_server_error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MaterialDownloadView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Material.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        return Response({'download_url': material.file_url})

class MaterialSearchView(generics.ListAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        if not query:
            return Material.objects.none()
        
        return Material.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(tags__icontains=query) |
            models.Q(course__name__icontains=query)
        )
