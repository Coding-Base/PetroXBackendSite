from django.contrib import admin
from django import forms
import uuid

from .models import MonetizationSettings, ActivationCode, UserActivation


@admin.register(MonetizationSettings)
class MonetizationSettingsAdmin(admin.ModelAdmin):
    list_display = ['is_enabled', 'price', 'whatsapp_number', 'updated_at']
    fields = ['is_enabled', 'price', 'payment_account', 'whatsapp_number']
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return MonetizationSettings.objects.count() == 0

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ActivationCode)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'is_used', 'used_by', 'created_at', 'used_at']
    list_filter = ['is_used', 'created_at', 'used_at']
    search_fields = ['code', 'used_by__username']
    readonly_fields = ['code', 'created_at', 'used_at', 'used_by']
    fields = ['code', 'is_used', 'used_by', 'created_at', 'used_at']

    def has_add_permission(self, request):
        # Keep default add permission (allowing admin UI add if needed)
        return True

    actions = ['mark_as_unused', 'generate_ten_codes', 'generate_twenty_codes', 'generate_fifty_codes']

    def mark_as_unused(self, request, queryset):
        """Allow admin to reset used codes"""
        updated = queryset.update(is_used=False, used_by=None, used_at=None)
        self.message_user(request, f'{updated} codes marked as unused')
    
    mark_as_unused.short_description = "Mark selected codes as unused"

    def _generate_n_codes(self, n):
        """Helper to generate n activation codes"""
        codes = []
        for _ in range(n):
            code = uuid.uuid4().hex[:12].upper()
            codes.append(ActivationCode(code=code))
        return ActivationCode.objects.bulk_create(codes)

    def generate_ten_codes(self, request, queryset):
        """Generate 10 activation codes"""
        self._generate_n_codes(10)
        self.message_user(request, '10 activation codes generated')
    
    generate_ten_codes.short_description = 'Generate 10 activation codes'

    def generate_twenty_codes(self, request, queryset):
        """Generate 20 activation codes"""
        self._generate_n_codes(20)
        self.message_user(request, '20 activation codes generated')
    
    generate_twenty_codes.short_description = 'Generate 20 activation codes'

    def generate_fifty_codes(self, request, queryset):
        """Generate 50 activation codes"""
        self._generate_n_codes(50)
        self.message_user(request, '50 activation codes generated')
    
    generate_fifty_codes.short_description = 'Generate 50 activation codes'

    def save_model(self, request, obj, form, change):
        """Ensure a generated code exists if admin adds via the regular add form."""
        if not obj.code:
            obj.code = uuid.uuid4().hex[:12].upper()
        super().save_model(request, obj, form, change)


@admin.register(UserActivation)
class UserActivationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'activated_at', 'created_at']
    list_filter = ['status', 'activated_at', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'created_at', 'updated_at', 'activated_at']
    
    def has_add_permission(self, request):
        # Add via API only
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    actions = ['unlock_user', 'lock_user']

    def unlock_user(self, request, queryset):
        """Admin action to unlock user"""
        updated = queryset.update(status='unlocked')
        self.message_user(request, f'{updated} users unlocked')
    
    unlock_user.short_description = "Unlock selected users"

    def lock_user(self, request, queryset):
        """Admin action to lock user"""
        updated = queryset.update(status='locked')
        self.message_user(request, f'{updated} users locked')
    
    lock_user.short_description = "Lock selected users"
