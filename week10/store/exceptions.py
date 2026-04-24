from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError


def custom_exception_handler(exc, context):
    """
    Catches DB errors and returns clean JSON instead of exposing internals.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Catch DB integrity errors (duplicate keys, constraint violations, etc.)
    if isinstance(exc, IntegrityError):
        return Response(
            {"error": "A database constraint was violated. Please check your data for duplicates."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Catch any other unhandled exceptions
    return Response(
        {"error": "An unexpected error occurred. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
