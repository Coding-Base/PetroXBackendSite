from rest_framework import serializers
from .models import ActivationCode, UserActivation, MonetizationSettings


class ActivationCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivationCode
        fields = ['id', 'code', 'is_used', 'used_by', 'created_at', 'used_at']
        read_only_fields = ['id', 'created_at', 'used_at']


class UserActivationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserActivation
        fields = ['id', 'username', 'email', 'status', 'activation_code', 'activated_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'activated_at']


class MonetizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonetizationSettings
        fields = ['id', 'is_enabled', 'price', 'payment_account', 'whatsapp_number']


class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, required=True)
