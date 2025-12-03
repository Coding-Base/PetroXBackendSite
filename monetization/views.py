from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ActivationCode, UserActivation, MonetizationSettings
from .serializers import (
    ActivationCodeSerializer,
    UserActivationSerializer,
    MonetizationSettingsSerializer,
    VerifyCodeSerializer
)


class MonetizationSettingsViewSet(viewsets.ModelViewSet):
    """Admin-only endpoint for monetization settings"""
    queryset = MonetizationSettings.objects.all()
    serializer_class = MonetizationSettingsSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        # Always get the first (and typically only) settings object
        obj, created = MonetizationSettings.objects.get_or_create()
        return obj

    def list(self, request):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def update(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivationCodeViewSet(viewsets.ModelViewSet):
    """Admin-only endpoint to generate and manage activation codes"""
    queryset = ActivationCode.objects.all()
    serializer_class = ActivationCodeSerializer
    permission_classes = [IsAdminUser]

    def create(self, request):
        """Generate a new activation code"""
        import secrets
        import string
        
        # Generate a random alphanumeric code
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
        
        activation_code = ActivationCode.objects.create(code=code)
        serializer = self.get_serializer(activation_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_create(self, request):
        """Generate multiple activation codes at once"""
        count = request.data.get('count', 1)
        
        if not isinstance(count, int) or count < 1 or count > 1000:
            return Response(
                {'error': 'Count must be between 1 and 1000'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            codes.append(ActivationCode(code=code))
        
        ActivationCode.objects.bulk_create(codes)
        return Response(
            {'message': f'{count} activation codes generated successfully'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def usage_stats(self, request):
        """Get statistics on code usage"""
        total = ActivationCode.objects.count()
        used = ActivationCode.objects.filter(is_used=True).count()
        unused = total - used
        
        return Response({
            'total_codes': total,
            'used_codes': used,
            'unused_codes': unused,
            'usage_percentage': (used / total * 100) if total > 0 else 0
        })


class UserActivationViewSet(viewsets.ModelViewSet):
    """Manage user activation statuses"""
    queryset = UserActivation.objects.all()
    serializer_class = UserActivationSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_status(self, request):
        """Get current user's activation status"""
        try:
            user_activation = UserActivation.objects.get(user=request.user)
        except UserActivation.DoesNotExist:
            # Create default locked status for new users
            user_activation = UserActivation.objects.create(
                user=request.user,
                status='locked'
            )
        
        serializer = self.get_serializer(user_activation)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def verify_code(self, request):
        """Verify and apply activation code for current user"""
        serializer = VerifyCodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        code_input = serializer.validated_data['code'].strip().upper()
        
        # Check if code exists and is valid
        try:
            activation_code = ActivationCode.objects.get(code=code_input, is_used=False)
        except ActivationCode.DoesNotExist:
            return Response(
                {'error': 'Invalid or already used activation code'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create user activation
        user_activation, created = UserActivation.objects.get_or_create(user=request.user)
        
        # Check if already unlocked
        if user_activation.status == 'unlocked':
            return Response(
                {'message': 'Your account is already unlocked', 'status': 'unlocked'},
                status=status.HTTP_200_OK
            )
        
        # Mark code as used and unlock user
        activation_code.is_used = True
        activation_code.used_by = request.user
        activation_code.used_at = timezone.now()
        activation_code.save()
        
        user_activation.unlock(activation_code)
        
        serializer = UserActivationSerializer(user_activation)
        return Response(
            {
                'message': 'Account activated successfully!',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def monetization_info(self, request):
        """Get monetization info for unauthenticated feature access"""
        try:
            settings = MonetizationSettings.objects.first()
        except MonetizationSettings.DoesNotExist:
            settings = MonetizationSettings.objects.create()
        
        serializer = MonetizationSettingsSerializer(settings)
        return Response(serializer.data)
