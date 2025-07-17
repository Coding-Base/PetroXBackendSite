from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from django.db import IntegrityError
from ..serializers import UserSerializer
from rest_framework.exceptions import ValidationError

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
        except IntegrityError:
            return Response(
                {"detail": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    



import json
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.conf import settings

class GoogleAuthView(APIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        # Get authorization code from request
        code = request.data.get('code')
        
        if not code:
            return Response({'detail': 'Authorization code is required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Exchange code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'code': code,
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'redirect_uri': 'postmessage',  # For SPAs
                'grant_type': 'authorization_code'
            }
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            
            token_json = token_response.json()
            id_token_str = token_json.get('id_token')
            
            # Verify ID token
            id_info = id_token.verify_oauth2_token(
                id_token_str, 
                google_requests.Request(), 
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # Validate token issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return Response({'detail': 'Invalid token issuer'}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create user
            email = id_info['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': id_info.get('given_name', ''),
                    'last_name': id_info.get('family_name', ''),
                }
            )
            
            # Create JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            })
            
        except Exception as e:
            return Response({'detail': str(e)}, 
                            status=status.HTTP_400_BAD_REQUEST)
