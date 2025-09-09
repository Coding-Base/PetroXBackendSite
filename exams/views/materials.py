from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException  # Changed import
from django.db import models
from django.utils import timezone
import logging
from ..models import Material
from ..serializers import MaterialSerializer
from exams.cloudinary_utils import get_cloudinary_signed_or_public_url
from rest_framework.generics import RetrieveAPIView


logger = logging.getLogger(__name__)

import cloudinary.uploader


class MaterialUploadView(generics.CreateAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def perform_create(self, serializer):
        material = serializer.save()

        if material.file:
            # Upload the file to Cloudinary as a PUBLIC asset
            upload_result = cloudinary.uploader.upload(
                material.file,
                resource_type="raw",   # required for PDFs/docs
                folder="materials",
                type="upload"          # ensures PUBLIC, not authenticated
            )

            # Store the public URL instead of local file path
            material.file = upload_result["secure_url"]
            material.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class MaterialDownloadView(RetrieveAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def retrieve(self, request, *args, **kwargs):
        material = self.get_object()
        download_url = get_cloudinary_signed_or_public_url(material)
        return Response({"download_url": download_url})

            
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





