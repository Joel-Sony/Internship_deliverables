from django.urls import path
from . import views

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/resend-otp/', views.ResendOTPView.as_view(), name='resend-otp')
]

