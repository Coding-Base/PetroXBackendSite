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
        uploaded_file = self.request.FILES.get("file")

        if not uploaded_file:
            raise ValueError("No file provided")

        # Upload to Cloudinary as PUBLIC
        upload_result = cloudinary.uploader.upload(
            uploaded_file,
            resource_type="raw",   # needed for PDFs/docs
            folder="materials",
            type="upload"          # makes it PUBLIC
        )

        # Save Material with Cloudinary URL
        serializer.save(
            uploaded_by=self.request.user,
            file=upload_result["secure_url"]
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
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







