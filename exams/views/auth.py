import logging
import requests
import re
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import GoogleAuthError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError
from django.db.utils import DataError
from ..serializers import UserSerializer
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

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
from rest_framework.renderers import JSONRenderer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class GoogleAuthView(APIView):
    permission_classes = []  # Allow unauthenticated access
    renderer_classes = [JSONRenderer]
    def post(self, request):
        # Get authorization code from request
        code = request.data.get('code')
        
        if not code:
            logger.warning("GoogleAuthView: Missing authorization code")
            return Response(
                {"error": "authorization_code_required", "message": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            logger.info(f"GoogleAuthView: Processing code {code[:10]}...")
            
            # Exchange code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'code': code,
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'redirect_uri': 'postmessage',
                'grant_type': 'authorization_code'
            }
            
            # Send request to Google
            token_response = requests.post(token_url, data=token_data, timeout=10)
            token_response.raise_for_status()
            
            token_json = token_response.json()
            id_token_str = token_json.get('id_token')
            
            if not id_token_str:
                logger.error("GoogleAuthView: Missing id_token in Google response")
                return Response(
                    {"error": "missing_id_token", "message": "Google authentication failed - missing id_token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify ID token
            try:
                id_info = id_token.verify_oauth2_token(
                    id_token_str, 
                    google_requests.Request(), 
                    settings.GOOGLE_OAUTH2_CLIENT_ID
                )
            except (ValueError, GoogleAuthError) as e:
                logger.error(f"GoogleAuthView: Token verification failed - {str(e)}")
                return Response(
                    {"error": "token_verification_failed", "message": "Invalid Google token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate token issuer
            if id_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"GoogleAuthView: Invalid token issuer - {id_info.get('iss')}")
                return Response(
                    {"error": "invalid_token_issuer", "message": "Invalid token issuer"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user email
            email = id_info.get('email')
            if not email:
                logger.error("GoogleAuthView: Missing email in token")
                return Response(
                    {"error": "missing_email", "message": "Google token doesn't contain email"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate username from email
            base_username = email.split('@')[0]
            username = self.generate_unique_username(base_username)
            
            # Get or create user
            try:
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'first_name': id_info.get('given_name', ''),
                        'last_name': id_info.get('family_name', ''),
                    }
                )
                
                if created:
                    logger.info(f"GoogleAuthView: Created new user for {email}")
                else:
                    logger.info(f"GoogleAuthView: Existing user found for {email}")
                    
            except IntegrityError:
                logger.warning(f"GoogleAuthView: Username conflict for {username}, retrying")
                # Retry with a different username if conflict occurs
                user = User.objects.get(email=email)
                
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
            }, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"GoogleAuthView: Network error - {str(e)}")
            return Response(
                {"error": "network_error", "message": "Failed to communicate with Google"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except (DataError, ValueError, KeyError) as e:
            logger.error(f"GoogleAuthView: Data processing error - {str(e)}")
            return Response(
                {"error": "data_processing_error", "message": "Error processing authentication data"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.exception("GoogleAuthView: Unexpected error")
            return Response(
                {"error": "server_error", "message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def generate_unique_username(self, base_username):
        """Generate a unique username by appending numbers if needed"""
        # Clean the username
        username = re.sub(r'[^\w.@+-]', '', base_username)[:30]
        counter = 1
        original_username = username
        
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                raise ValueError("Could not generate unique username")
                
        return username