from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from ..models import Material
from ..serializers import MaterialSerializer

class MaterialUploadView(generics.CreateAPIView):
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            material = serializer.save(uploaded_by=request.user)
            if hasattr(material.file, 'close'):
                material.file.close()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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