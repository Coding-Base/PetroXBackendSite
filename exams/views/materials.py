from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException  # Changed import
from django.db import models
from django.utils import timezone
import logging
from ..models import Material
from ..serializers import MaterialSerializer

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
        
        # Exception handling updated to use APIException
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
            # Handle all other exceptions, including storage service issues
            logger.exception("Unexpected upload error")
            
            # Create a proper 503 Service Unavailable response
            return Response({
                "error": "storage_unavailable",
                "message": "Storage service is currently unavailable. Please try again later."
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class MaterialDownloadView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Material.objects.all()

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        try:
            download_url = get_cloudinary_signed_or_public_url(material)
            if not download_url:
                return Response({'detail': 'Download URL not available'}, status=status.HTTP_404_NOT_FOUND)
            # Return the (possibly signed) URL as JSON so the front-end can open it
            return Response({'download_url': download_url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Error generating download URL")
            return Response({'detail': 'Failed to generate download URL'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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

