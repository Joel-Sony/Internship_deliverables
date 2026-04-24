import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        return timezone.now() > self.created_at + timedelta(minutes=expiry_minutes)

    @staticmethod
    def generate_otp(user):
        """Invalidate old OTPs and create a new one."""
        OTP.objects.filter(user=user, is_used=False).update(is_used=True)
        code = str(random.randint(100000, 999999))
        return OTP.objects.create(user=user, code=code)

    def __str__(self):
        return f"OTP {self.code} for {self.user.username}"
