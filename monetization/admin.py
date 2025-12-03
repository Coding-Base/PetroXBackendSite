from django.contrib import admin
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
    
    def has_add_permission(self, request):
        # Add codes via bulk_create API only
        return False

    actions = ['mark_as_unused']

    def mark_as_unused(self, request, queryset):
        """Allow admin to reset used codes"""
        updated = queryset.update(is_used=False, used_by=None, used_at=None)
        self.message_user(request, f'{updated} codes marked as unused')
    
    mark_as_unused.short_description = "Mark selected codes as unused"


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
