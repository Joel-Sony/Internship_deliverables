import jwt
import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import CustomUser, OTP
from .serializers import RegisterSerializer, LoginSerializer, OTPVerifySerializer


def generate_jwt(user):
    """Generate a JWT token for the given user."""
    payload = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def send_otp_email(user, otp_code):
    """Send OTP via email (prints to console in dev)."""
    send_mail(
        subject='Your Login OTP',
        message=f'Your OTP code is: {otp_code}. It expires in {settings.OTP_EXPIRY_MINUTES} minutes.',
        from_email='noreply@auth.com',
        recipient_list=[user.email],
    )


class RegisterView(APIView):
    """Register a new user with hashed password."""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except Exception:
                return Response(
                    {'error': 'An unexpected error occurred during registration. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({
                'message': 'User registered successfully',
                'user': {'username': user.username, 'email': user.email, 'role': user.role}
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Validate credentials, enforce lockout, and send OTP."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if account is locked
        if user.is_locked:
            return Response({
                'error': 'Account is locked due to too many failed attempts. Contact admin.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                user.locked_at = timezone.now()
                user.save()
                return Response({
                    'error': 'Account locked after 5 failed attempts. Contact admin.'
                }, status=status.HTTP_403_FORBIDDEN)
            user.save()
            return Response({
                'error': f'Invalid credentials. {settings.MAX_FAILED_ATTEMPTS - user.failed_login_attempts} attempts remaining.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Reset failed attempts on successful password check
        user.failed_login_attempts = 0
        user.save()

        # Generate and send OTP
        otp = OTP.generate_otp(user)
        send_otp_email(user, otp.code)

        return Response({
            'message': 'OTP sent to your email. Please verify to complete login.'
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """Verify OTP and return JWT token."""

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        otp_code = serializer.validated_data['otp']

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid user'}, status=status.HTTP_404_NOT_FOUND)

        # Find the latest unused OTP for this user
        try:
            otp = OTP.objects.filter(user=user, code=otp_code, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used and generate JWT
        otp.is_used = True
        otp.save()
    
        token = generate_jwt(user)
        return Response({
            'message': 'Login successful',
            'token': token,
            'user': {'username': user.username, 'role': user.role}
        }, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """Resend a new OTP to the user's email."""

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_locked:
            return Response({'error': 'Account is locked'}, status=status.HTTP_403_FORBIDDEN)

        otp = OTP.generate_otp(user)
        send_otp_email(user, otp.code)

        return Response({'message': 'New OTP sent to your email.'}, status=status.HTTP_200_OK)

