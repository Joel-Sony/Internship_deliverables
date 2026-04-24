from django.contrib import admin
from .models import CustomUser, OTP


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_locked', 'failed_login_attempts']
    list_filter = ['role', 'is_locked']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'is_used']
    list_filter = ['is_used']
