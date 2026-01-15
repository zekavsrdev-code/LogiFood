"""
Utility functions for the application
"""
from typing import Dict, Any
from rest_framework.response import Response
from rest_framework import status


def success_response(data: Any = None, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
    """Standard success response"""
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(message: str = "Error", errors: Dict[str, Any] = None, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """Standard error response"""
    response_data = {
        'success': False,
        'message': message,
    }
    if errors:
        response_data['errors'] = errors
    return Response(response_data, status=status_code)
