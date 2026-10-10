from django.contrib import admin

from .models import AuditLog, LoginAttempt, UserSecurityProfile


@admin.register(UserSecurityProfile)
class UserSecurityProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'totp_enabled', 'dark_mode')
    search_fields = ('user__username', 'user__email')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'successful', 'created_at')
    list_filter = ('successful', 'created_at')
    search_fields = ('username', 'ip_address')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'action')

# Register your models here.
