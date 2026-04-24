import jwt
from django.conf import settings
from django.http import JsonResponse


# Path prefix -> list of allowed roles
ROLE_REQUIREMENTS = {
    '/api/admin/': ['admin'],
    '/api/moderator/': ['admin', 'moderator'],
    '/api/user/': ['admin', 'moderator', 'user'],
}


class RolePermissionMiddleware:
    """Decodes JWT and enforces role-based access on protected paths."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.jwt_user = None

        # Decode JWT if present
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                request.jwt_user = payload
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=401)

        # Check role requirements for the current path
        for path_prefix, allowed_roles in ROLE_REQUIREMENTS.items():
            if request.path.startswith(path_prefix):
                if not request.jwt_user:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                if request.jwt_user.get('role') not in allowed_roles:
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                break

        return self.get_response(request)
